from celery import shared_task
from django.utils import timezone
from django.db import transaction
import time
import logging

from .models import SimulationScenario, SimulationResult, PredictiveModel

logger = logging.getLogger(__name__)


# =====================================================
# Run Simulation Task
# =====================================================
@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=10, retry_kwargs={'max_retries': 3})
def run_simulation_task(self, scenario_id):
    """
    Execute a simulation scenario and generate results.
    """
    try:
        with transaction.atomic():
            scenario = SimulationScenario.objects.select_for_update().get(id=scenario_id)

            # Prevent duplicate execution
            if scenario.status in ['running', 'completed']:
                logger.warning(f"Simulation {scenario_id} already executed or running.")
                return None

            scenario.status = 'running'
            scenario.actual_start = timezone.now()
            scenario.save(update_fields=['status', 'actual_start'])

        # ----------------------------
        # Simulate execution
        # ----------------------------
        start_time = time.time()
        time.sleep(5)  # simulation placeholder
        execution_time = round(time.time() - start_time, 2)

        # ----------------------------
        # Create result
        # ----------------------------
        result = SimulationResult.objects.create(
            scenario=scenario,
            metrics={
                'execution_time': execution_time,
                'success_rate': 1.0,
                'warnings': 0,
                'errors': 0,
            },
            time_series_data={},
            conclusions='Simulation completed successfully',
            recommendations=[
                'Optimize parameters for improved efficiency',
                'Run scenario with extended constraints'
            ],
            risk_assessment={'overall_risk': 'low'},
            execution_time=execution_time,
            memory_usage=1024.5,
        )

        # ----------------------------
        # Mark scenario completed
        # ----------------------------
        scenario.status = 'completed'
        scenario.actual_end = timezone.now()
        scenario.save(update_fields=['status', 'actual_end'])

        logger.info(f"Simulation completed: {scenario_id}")
        return str(result.id)

    except SimulationScenario.DoesNotExist:
        logger.error(f"SimulationScenario not found: {scenario_id}")
        return None

    except Exception as exc:
        logger.exception(f"Simulation failed: {scenario_id}")

        SimulationScenario.objects.filter(id=scenario_id).update(
            status='failed',
            actual_end=timezone.now()
        )

        raise exc


# =====================================================
# Train Predictive Model Task
# =====================================================
@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=15, retry_kwargs={'max_retries': 3})
def train_model_task(self, model_id):
    """
    Train a predictive model asynchronously.
    """
    try:
        with transaction.atomic():
            model = PredictiveModel.objects.select_for_update().get(id=model_id)

            # Prevent duplicate training
            if model.status == 'active':
                logger.warning(f"Model {model_id} already trained.")
                return str(model.id)

            model.status = 'training'
            model.save(update_fields=['status'])

        # ----------------------------
        # Simulate training
        # ----------------------------
        start_time = time.time()
        time.sleep(10)  # training placeholder
        duration = round(time.time() - start_time, 2)

        # ----------------------------
        # Update trained model
        # ----------------------------
        model.status = 'active'
        model.trained_at = timezone.now()
        model.training_duration = duration

        # ML metrics (0–1 enforced)
        model.accuracy = 0.92
        model.precision = 0.89
        model.recall = 0.94
        model.f1_score = round(
            2 * (model.precision * model.recall) / (model.precision + model.recall),
            3
        )

        model.save()

        logger.info(f"Model training completed: {model_id}")
        return str(model.id)

    except PredictiveModel.DoesNotExist:
        logger.error(f"PredictiveModel not found: {model_id}")
        return None

    except Exception as exc:
        logger.exception(f"Model training failed: {model_id}")

        PredictiveModel.objects.filter(id=model_id).update(
            status='inactive'
        )

        raise exc
