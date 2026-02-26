"""
SAGA Orchestrator for Flight Booking - Fixed Implementation
"""
import logging
import uuid
import requests
from typing import Dict, Any
from .saga_log_storage import saga_log_storage
from .failed_booking_handler import create_failed_booking_record

logger = logging.getLogger(__name__)

class SagaStep:
    def __init__(self, name: str, action_url: str, compensation_url: str):
        self.name = name
        self.action_url = action_url
        self.compensation_url = compensation_url

class BookingOrchestrator:
    def __init__(self):
        # Step order (RESTRUCTURED):
        # 1) Miles Loyalty
        # 2) Payment Transaction
        # 3) Booking Done
        # 4) Reservation Done
        #
        # NOTE: Per requirements, this is a control-step restructure only:
        # - Keep existing endpoints and underlying business logic intact.
        # - Compensation flows remain the same, but now map to the new step order.
        self.steps = [
            # Step 1: Miles Loyalty (was AwardMiles)
            SagaStep("MilesLoyalty",
                    "http://localhost:8003/api/saga/award-miles/",
                    "http://localhost:8003/api/saga/reverse-miles/"),
            # Step 2: Payment Transaction (was AuthorizePayment)
            SagaStep("PaymentTransaction",
                    "http://localhost:8002/api/saga/authorize-payment/",
                    "http://localhost:8002/api/saga/cancel-payment/"),
            # Step 3: Booking Done (was ConfirmBooking)
            SagaStep("BookingDone",
                    "http://localhost:8001/api/saga/confirm-booking/",
                    "http://localhost:8001/api/saga/cancel-booking/"),
            # Step 4: Reservation Done (was ReserveSeat)
            SagaStep("ReservationDone",
                    "http://localhost:8001/api/saga/reserve-seat/",
                    "http://localhost:8001/api/saga/cancel-seat/")
        ]
    
    def start_booking_saga(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        correlation_id = booking_data.get("correlation_id") or str(uuid.uuid4())
        logger.info(f"[SAGA] Starting booking SAGA with correlation_id: {correlation_id} (provided={bool(booking_data.get('correlation_id'))})")
        
        # DIAGNOSTIC: Add comprehensive logging for debugging missing logs
        logger.info(f"[SAGA ORCHESTRATOR DEBUG] ===== SAGA TRANSACTION START =====")
        logger.info(f"[SAGA ORCHESTRATOR DEBUG] Correlation ID: {correlation_id}")
        logger.info(f"[SAGA ORCHESTRATOR DEBUG] Flight ID: {booking_data.get('flight_id')}")
        logger.info(f"[SAGA ORCHESTRATOR DEBUG] User ID: {booking_data.get('user_id')}")
        
        # Add initial log entry
        saga_log_storage.add_log(
            correlation_id, "SAGA_START", "UI Service", "info",
            f"📝 Demo SAGA transaction created for correlation_id: {correlation_id}"
        )
        
        # DIAGNOSTIC: Verify initial log was added
        initial_logs = saga_log_storage.get_logs(correlation_id)
        logger.info(f"[SAGA ORCHESTRATOR DEBUG] Initial logs count after SAGA_START: {len(initial_logs)}")
        
        logger.info(f"[PAYMENT_FLOW_DEBUG] ===== SAGA ORCHESTRATOR ENTRY =====")
        logger.info(f"[PAYMENT_FLOW_DEBUG] Received booking_data keys: {list(booking_data.keys())}")
        logger.info(f"[PAYMENT_FLOW_DEBUG] flight_id in booking_data: '{booking_data.get('flight_id')}'")
        logger.info(f"[PAYMENT_FLOW_DEBUG] user_id in booking_data: {booking_data.get('user_id')}")
        logger.info(f"[PAYMENT_FLOW_DEBUG] passengers count: {len(booking_data.get('passengers', []))}")
        
        completed_steps = []
        try:
            for i, step in enumerate(self.steps):
                logger.info(f"[SAGA] Executing step {i+1}/{len(self.steps)}: {step.name}")
                
                # DIAGNOSTIC: Add comprehensive step logging
                logger.info(f"[SAGA ORCHESTRATOR DEBUG] ===== STEP {i+1}: {step.name} =====")
                logger.info(f"[SAGA ORCHESTRATOR DEBUG] Step URL: {step.action_url}")
                
                # Log step initiation with proper service name
                saga_log_storage.add_log(
                    correlation_id, step.name, f"{step.name} Service", "info",
                    f"{step.name} step initiated for correlation_id: {correlation_id}"
                )
                
                # DIAGNOSTIC: Check logs count after step initiation
                current_logs = saga_log_storage.get_logs(correlation_id)
                logger.info(f"[SAGA ORCHESTRATOR DEBUG] Logs count after {step.name} initiation: {len(current_logs)}")
                
                logger.info(f"[PAYMENT_FLOW_DEBUG] ===== SAGA STEP {i+1}: {step.name} =====")
                logger.info(f"[PAYMENT_FLOW_DEBUG] Step URL: {step.action_url}")
                
                # Backwards-compatible simulation flags:
                # Existing callers send flags like simulate_awardmiles_fail, etc.
                simulate_flag_aliases = {
                    "MilesLoyalty": "awardmiles",
                    "PaymentTransaction": "authorizepayment",
                    "BookingDone": "confirmbooking",
                    "ReservationDone": "reserveseat",
                }
                simulate_key = simulate_flag_aliases.get(step.name, step.name.lower())
                step_data = {
                    "correlation_id": correlation_id,
                    "step_number": i + 1,
                    "booking_data": booking_data,
                    "simulate_failure": booking_data.get(f"simulate_{simulate_key}_fail", False)
                }
                
                logger.info(f"[PAYMENT_FLOW_DEBUG] Step data flight_id: '{step_data['booking_data'].get('flight_id')}'")
                logger.info(f"[PAYMENT_FLOW_DEBUG] Simulate failure: {step_data['simulate_failure']}")
                
                result = self._execute_step(step, step_data)
                
                # DIAGNOSTIC: Log step execution result
                logger.info(f"[SAGA ORCHESTRATOR DEBUG] Step {step.name} result: {result}")
                
                if result.get("success"):
                    completed_steps.append(step)
                    logger.info(f"[SAGA] Step {step.name} completed successfully")
                    
                    # Log step success with detailed information from the actual response
                    step_message = result.get('message', f'Step {step.name} completed successfully')
                    saga_log_storage.add_log(
                        correlation_id, step.name, f"{step.name} Service", "success",
                        f"✅ {step_message}"
                    )
                    
                    # DIAGNOSTIC: Check logs count after step success
                    current_logs = saga_log_storage.get_logs(correlation_id)
                    logger.info(f"[SAGA ORCHESTRATOR DEBUG] Logs count after {step.name} success: {len(current_logs)}")
                    
                    # Add specific step details based on step type (updated step names only)
                    if step.name == "ReservationDone" and result.get('reservation_id'):
                        saga_log_storage.add_log(
                            correlation_id, step.name, "Backend Service", "info",
                            f"💺 Created reservation record: {result.get('reservation_id')}"
                        )
                    elif step.name == "PaymentTransaction" and result.get('authorization_id'):
                        saga_log_storage.add_log(
                            correlation_id, step.name, "Payment Service", "info",
                            f"💳 Authorization ID: {result.get('authorization_id')} - Amount: ${result.get('amount', 0)}"
                        )
                        saga_log_storage.add_log(
                            correlation_id, step.name, "Payment Service", "info",
                            "INTER-SERVICE: Payment authorized. UI should now collect card details / confirm capture."
                        )
                    elif step.name == "MilesLoyalty" and result.get('miles_awarded'):
                        if result.get('is_round_trip') and result.get('flight1_miles') and result.get('flight2_miles'):
                            f1 = result.get('flight1_miles')
                            f2 = result.get('flight2_miles')
                            total = result.get('miles_awarded')
                            saga_log_storage.add_log(
                                correlation_id, step.name, "Loyalty Service", "info",
                                f"🏆 Round trip miles: {f1} (Outbound) + {f2} (Return) = {total} total pts | Balance: {result.get('original_balance')} -> {result.get('new_balance')}"
                            )
                        else:
                            saga_log_storage.add_log(
                                correlation_id, step.name, "Loyalty Service", "info",
                                f"🏆 Miles awarded: {result.get('miles_awarded')} | Balance: {result.get('original_balance')} -> {result.get('new_balance')}"
                            )
                else:
                    logger.error(f"[SAGA] Step {step.name} failed: {result.get('error', 'Unknown error')}")
                    
                    # Log step failure with clear indication
                    saga_log_storage.add_log(
                        correlation_id, step.name, "ORCHESTRATOR", "error",
                        f"❌ Step {step.name} failed: {result.get('error', 'Unknown error')}"
                    )
                    
                    # DIAGNOSTIC: Check logs count after step failure
                    current_logs = saga_log_storage.get_logs(correlation_id)
                    logger.info(f"[SAGA ORCHESTRATOR DEBUG] Logs count after {step.name} failure: {len(current_logs)}")
                    
                    compensation_result = self._execute_compensation(completed_steps, correlation_id, booking_data)
                    
                    # DIAGNOSTIC: Check logs count after compensation
                    final_logs = saga_log_storage.get_logs(correlation_id)
                    logger.info(f"[SAGA ORCHESTRATOR DEBUG] Final logs count after compensation: {len(final_logs)}")
                    
                    # Create failed booking record for user to see in their bookings
                    error_message = f"SAGA failed at step {step.name}: {result.get('error', 'Unknown error')}"
                    logger.error(f"[SAGA ORCHESTRATOR] 🚨 SAGA FAILURE DETECTED - About to create failed booking record")
                    logger.error(f"[SAGA ORCHESTRATOR] 📊 User ID: {booking_data.get('user_id')}")
                    logger.error(f"[SAGA ORCHESTRATOR] 🎫 Flight ID: {booking_data.get('flight_id')}")
                    logger.error(f"[SAGA ORCHESTRATOR] ❌ Failed step: {step.name}")
                    logger.error(f"[SAGA ORCHESTRATOR] 💬 Error message: {error_message}")
                    
                    failed_ticket = create_failed_booking_record(
                        correlation_id=correlation_id,
                        booking_data=booking_data,
                        failed_step=step.name,
                        error_message=error_message,
                        compensation_result=compensation_result
                    )
                    
                    logger.info(f"[SAGA ORCHESTRATOR] 📝 Failed booking handler returned: {failed_ticket}")
                    if failed_ticket:
                        logger.info(f"[SAGA ORCHESTRATOR] ✅ Failed booking record created with ref: {failed_ticket.get('ref_no')}")
                    else:
                        logger.error(f"[SAGA ORCHESTRATOR] ❌ Failed booking handler returned None - no record created!")
                    
                    return {
                        "success": False,
                        "correlation_id": correlation_id,
                        "error": error_message,
                        "failed_step": step.name,
                        "compensation_result": compensation_result,
                        "failed_booking_ref": failed_ticket.get('ref_no') if failed_ticket else None
                    }
            
            logger.info(f"[SAGA] All steps completed successfully for correlation_id: {correlation_id}")
            
            return {
                "success": True,
                "correlation_id": correlation_id,
                "message": "SAGA completed successfully",
                "steps_completed": len(self.steps)
            }
            
        except Exception as e:
            logger.error(f"[SAGA] Unexpected error in SAGA execution: {e}")
            compensation_result = self._execute_compensation(completed_steps, correlation_id, booking_data)
            
            # Create failed booking record for unexpected errors too
            error_message = f"SAGA execution error: {str(e)}"
            failed_ticket = create_failed_booking_record(
                correlation_id=correlation_id,
                booking_data=booking_data,
                failed_step="UNEXPECTED_ERROR",
                error_message=error_message,
                compensation_result=compensation_result
            )
            
            logger.info(f"[SAGA] Created failed booking record for exception: {failed_ticket.get('ref_no') if failed_ticket else 'None'}")
            
            return {
                "success": False,
                "correlation_id": correlation_id,
                "error": error_message,
                "compensation_result": compensation_result,
                "failed_booking_ref": failed_ticket.get('ref_no') if failed_ticket else None
            }
    
    def _execute_step(self, step: SagaStep, step_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info(f"[SAGA] Calling {step.action_url}")
            response = requests.post(step.action_url, json=step_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"[SAGA] Step {step.name} response: {result}")
                return result
            else:
                logger.error(f"[SAGA] Step {step.name} HTTP error: {response.status_code}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
        except Exception as e:
            logger.error(f"[SAGA] Step {step.name} error: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_compensation(self, completed_steps: list, correlation_id: str, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[SAGA COMPENSATION] 🔄 Starting compensation for {len(completed_steps)} completed steps")
        logger.info(f"[SAGA COMPENSATION] 📋 Steps to compensate: {[step.name for step in completed_steps]}")
        
        # DIAGNOSTIC: Check logs before compensation
        pre_comp_logs = saga_log_storage.get_logs(correlation_id)
        logger.info(f"[SAGA ORCHESTRATOR DEBUG] Logs count before compensation: {len(pre_comp_logs)}")
        
        # Log compensation initiation
        saga_log_storage.add_log(
            correlation_id, "COMPENSATION", "ORCHESTRATOR", "warning",
            f"🔄 Starting compensation for {len(completed_steps)} completed steps"
        )
        
        # DIAGNOSTIC: Check logs after compensation initiation
        post_init_logs = saga_log_storage.get_logs(correlation_id)
        logger.info(f"[SAGA ORCHESTRATOR DEBUG] Logs count after compensation initiation: {len(post_init_logs)}")
        
        compensation_results = []
        for step in reversed(completed_steps):
            try:
                logger.info(f"[SAGA COMPENSATION] ⚡ Executing compensation for step: {step.name}")
                logger.info(f"[SAGA COMPENSATION] 🌐 Calling compensation URL: {step.compensation_url}")
                
                # DIAGNOSTIC: Add detailed logging for compensation debugging
                logger.info(f"[COMPENSATION_DEBUG] ===== COMPENSATION ATTEMPT =====")
                logger.info(f"[COMPENSATION_DEBUG] Step: {step.name}")
                logger.info(f"[COMPENSATION_DEBUG] URL: {step.compensation_url}")
                logger.info(f"[COMPENSATION_DEBUG] Correlation ID: {correlation_id}")
                logger.info(f"[COMPENSATION_DEBUG] Timeout: 30 seconds")
                
                compensation_data = {
                    "correlation_id": correlation_id,
                    "booking_data": booking_data,
                    "compensation_reason": f"SAGA failure - rolling back {step.name}"
                }
                
                logger.info(f"[COMPENSATION_DEBUG] Request payload: {compensation_data}")
                
                # Add connection test before actual request
                import time
                start_time = time.time()
                
                try:
                    response = requests.post(step.compensation_url, json=compensation_data, timeout=30)
                    end_time = time.time()
                    logger.info(f"[COMPENSATION_DEBUG] Request completed in {end_time - start_time:.2f} seconds")
                    logger.info(f"[COMPENSATION_DEBUG] Response status: {response.status_code}")
                    logger.info(f"[COMPENSATION_DEBUG] Response text: {response.text}")
                except requests.exceptions.RequestException as req_error:
                    logger.error(f"[COMPENSATION_DEBUG] Request failed: {req_error}")
                    raise req_error
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"[SAGA COMPENSATION] ✅ Compensation for {step.name} successful: {result.get('message', 'No message')}")
                    
                    # Log detailed compensation with actual results
                    comp_message = result.get('message', f'Compensation for {step.name} completed successfully')
                    saga_log_storage.add_log(
                        correlation_id, f"COMPENSATE_{step.name}", f"{step.name} Compensation", "success",
                        f"🔄 {comp_message}", is_compensation=True
                    )
                    
                    # DIAGNOSTIC: Check logs count after each compensation
                    comp_logs = saga_log_storage.get_logs(correlation_id)
                    logger.info(f"[SAGA ORCHESTRATOR DEBUG] Logs count after {step.name} compensation: {len(comp_logs)}")
                    
                    # Add specific compensation details (updated step names only)
                    if step.name == "MilesLoyalty" and result.get('miles_reversed'):
                        reversed_total = result.get('miles_reversed')
                        orig = result.get('original_balance')
                        new_bal = result.get('new_balance')
                        awards_count = result.get('awards_reversed', 1)
                        if awards_count > 1:
                            per_leg = reversed_total // awards_count
                            detail_msg = f"↩️ Round trip miles reversed: {per_leg} (Outbound) + {per_leg} (Return) = {reversed_total} total | Balance: {orig} -> {new_bal}"
                        else:
                            detail_msg = f"↩️ Miles reversed: {reversed_total} | Balance: {orig} -> {new_bal}"
                        saga_log_storage.add_log(
                            correlation_id, f"COMPENSATE_{step.name}", "Loyalty Compensation", "info",
                            detail_msg, is_compensation=True
                        )
                    elif step.name == "PaymentTransaction" and result.get('authorization_id'):
                        saga_log_storage.add_log(
                            correlation_id, f"COMPENSATE_{step.name}", "Payment Compensation", "info",
                            f"💳 Cancelled authorization: {result.get('authorization_id')} - Amount: ${result.get('amount', 0)}", is_compensation=True
                        )
                    elif step.name == "ReservationDone":
                        saga_log_storage.add_log(
                            correlation_id, f"COMPENSATE_{step.name}", "Backend Compensation", "info",
                            f"💺 Seat reservation cancelled successfully", is_compensation=True
                        )
                    
                    compensation_results.append({
                        "step": step.name,
                        "success": True,
                        "result": result,
                        "timestamp": str(uuid.uuid4())[:8]  # Simple timestamp for demo
                    })
                else:
                    logger.error(f"[SAGA COMPENSATION] ❌ Compensation for {step.name} failed: HTTP {response.status_code}")
                    
                    # Log failed compensation
                    saga_log_storage.add_log(
                        correlation_id, f"COMPENSATE_{step.name}", "ORCHESTRATOR", "error",
                        f"Compensation for {step.name} failed: HTTP {response.status_code}", is_compensation=True
                    )
                    
                    compensation_results.append({
                        "step": step.name,
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "timestamp": str(uuid.uuid4())[:8]
                    })
                    
            except Exception as e:
                logger.error(f"[SAGA] Compensation for {step.name} error: {e}")
                compensation_results.append({
                    "step": step.name,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "total_compensations": len(compensation_results),
            "successful_compensations": len([r for r in compensation_results if r.get("success")]),
            "results": compensation_results
        }