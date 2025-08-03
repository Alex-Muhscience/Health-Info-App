"""
Smart Appointment Scheduling & Queue Management System
AI-powered scheduling optimization with real-time queue management
"""

from datetime import datetime, timedelta, time, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
from sqlalchemy import and_, or_, func, text
from backend.database import db
from backend.models import Appointment, Client, Staff, Department
import heapq
import math

class AppointmentPriority(Enum):
    """Appointment priority levels"""
    ROUTINE = 1
    URGENT = 2
    EMERGENCY = 3
    FOLLOW_UP = 4

class SchedulingAlgorithm(Enum):
    """Scheduling optimization algorithms"""
    FIRST_AVAILABLE = "first_available"
    BALANCED_WORKLOAD = "balanced_workload"
    PATIENT_PREFERENCE = "patient_preference"
    AI_OPTIMIZED = "ai_optimized"

@dataclass
class TimeSlot:
    """Represents an available time slot"""
    start_time: datetime
    end_time: datetime
    provider_id: str
    department_id: str
    slot_type: str = "standard"  # standard, extended, emergency
    is_available: bool = True
    buffer_time: int = 15  # minutes

@dataclass
class SchedulingPreference:
    """Patient scheduling preferences"""
    patient_id: str
    preferred_providers: List[str] = field(default_factory=list)
    preferred_times: List[str] = field(default_factory=list)  # morning, afternoon, evening
    preferred_days: List[int] = field(default_factory=list)  # 0=Monday, 6=Sunday
    avoid_days: List[int] = field(default_factory=list)
    max_wait_time: int = 30  # minutes
    language_preference: Optional[str] = None
    accessibility_needs: List[str] = field(default_factory=list)

@dataclass
class QueueEntry:
    """Patient queue entry"""
    id: str
    patient_id: str
    appointment_id: str
    arrival_time: datetime
    estimated_wait_time: int  # minutes
    priority: AppointmentPriority
    status: str = "waiting"  # waiting, in_progress, completed, no_show
    queue_position: int = 0
    check_in_time: Optional[datetime] = None
    called_time: Optional[datetime] = None

class SmartSchedulingEngine:
    """Advanced appointment scheduling engine with AI optimization"""
    
    def __init__(self):
        self.scheduling_algorithm = SchedulingAlgorithm.AI_OPTIMIZED
        self.default_appointment_duration = 30  # minutes
        self.buffer_time = 15  # minutes between appointments
        self.max_daily_appointments_per_provider = 20
    
    def find_optimal_appointment_slot(
        self, 
        patient_id: str,
        provider_id: Optional[str] = None,
        department_id: Optional[str] = None,
        appointment_type: str = "consultation",
        duration_minutes: int = 30,
        priority: AppointmentPriority = AppointmentPriority.ROUTINE,
        preferred_date: Optional[date] = None,
        max_days_ahead: int = 30
    ) -> Optional[Dict[str, Any]]:
        """Find the optimal appointment slot using AI optimization"""
        
        # Get patient preferences
        preferences = self._get_patient_preferences(patient_id)
        
        # Get available providers
        available_providers = self._get_available_providers(
            department_id, provider_id, appointment_type
        )
        
        # Generate time slots
        time_slots = self._generate_available_slots(
            available_providers, 
            preferred_date or date.today(),
            max_days_ahead,
            duration_minutes
        )
        
        # Apply scheduling algorithm
        if self.scheduling_algorithm == SchedulingAlgorithm.AI_OPTIMIZED:
            optimal_slot = self._ai_optimize_scheduling(
                time_slots, preferences, priority, appointment_type
            )
        elif self.scheduling_algorithm == SchedulingAlgorithm.BALANCED_WORKLOAD:
            optimal_slot = self._balance_workload_scheduling(time_slots)
        elif self.scheduling_algorithm == SchedulingAlgorithm.PATIENT_PREFERENCE:
            optimal_slot = self._preference_based_scheduling(time_slots, preferences)
        else:  # FIRST_AVAILABLE
            optimal_slot = self._first_available_scheduling(time_slots)
        
        if optimal_slot:
            return {
                'slot': optimal_slot,
                'estimated_wait_time': self._estimate_wait_time(optimal_slot),
                'confidence_score': self._calculate_confidence_score(optimal_slot, preferences),
                'alternative_slots': self._get_alternative_slots(time_slots, optimal_slot, 3)
            }
        
        return None
    
    def _ai_optimize_scheduling(
        self, 
        time_slots: List[TimeSlot], 
        preferences: SchedulingPreference,
        priority: AppointmentPriority,
        appointment_type: str
    ) -> Optional[TimeSlot]:
        """AI-powered scheduling optimization"""
        
        if not time_slots:
            return None
        
        # Scoring factors
        scored_slots = []
        
        for slot in time_slots:
            score = 0
            
            # Provider preference score (30% weight)
            if slot.provider_id in preferences.preferred_providers:
                score += 30
            
            # Time preference score (25% weight)
            hour = slot.start_time.hour
            if "morning" in preferences.preferred_times and 8 <= hour < 12:
                score += 25
            elif "afternoon" in preferences.preferred_times and 12 <= hour < 17:
                score += 25
            elif "evening" in preferences.preferred_times and 17 <= hour < 20:
                score += 25
            
            # Day preference score (20% weight)
            weekday = slot.start_time.weekday()
            if weekday in preferences.preferred_days:
                score += 20
            if weekday in preferences.avoid_days:
                score -= 15
            
            # Priority adjustment (15% weight)
            if priority == AppointmentPriority.EMERGENCY:
                # Prefer earlier slots for emergencies
                days_from_now = (slot.start_time.date() - date.today()).days
                score += max(0, 15 - days_from_now * 2)
            elif priority == AppointmentPriority.FOLLOW_UP:
                # Follow-ups can be scheduled further out
                days_from_now = (slot.start_time.date() - date.today()).days
                if days_from_now >= 7:
                    score += 10
            
            # Provider workload balance (10% weight)
            workload_factor = self._get_provider_workload_factor(slot.provider_id, slot.start_time.date())
            score += (1 - workload_factor) * 10
            
            scored_slots.append((score, slot))
        
        # Return the highest scoring slot
        scored_slots.sort(key=lambda x: x[0], reverse=True)
        return scored_slots[0][1] if scored_slots else None
    
    def _get_provider_workload_factor(self, provider_id: str, appointment_date: date) -> float:
        """Calculate provider workload factor for the given date (0-1, where 1 is fully booked)"""
        daily_appointments = db.session.query(func.count(Appointment.id)).filter(
            Appointment.doctor_id == provider_id,
            func.date(Appointment.date) == appointment_date,
            Appointment.status.in_(['scheduled', 'confirmed'])
        ).scalar() or 0
        
        return min(daily_appointments / self.max_daily_appointments_per_provider, 1.0)
    
    def _generate_available_slots(
        self, 
        providers: List[Dict], 
        start_date: date, 
        max_days: int,
        duration_minutes: int
    ) -> List[TimeSlot]:
        """Generate available appointment slots"""
        
        slots = []
        current_date = start_date
        end_date = start_date + timedelta(days=max_days)
        
        while current_date <= end_date:
            # Skip weekends for routine appointments (configurable)
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                for provider in providers:
                    provider_slots = self._generate_provider_daily_slots(
                        provider, current_date, duration_minutes
                    )
                    slots.extend(provider_slots)
            
            current_date += timedelta(days=1)
        
        return slots
    
    def _generate_provider_daily_slots(
        self, 
        provider: Dict, 
        appointment_date: date,
        duration_minutes: int
    ) -> List[TimeSlot]:
        """Generate daily slots for a specific provider"""
        
        slots = []
        
        # Standard working hours (configurable per provider)
        work_hours = [
            (time(9, 0), time(12, 0)),   # Morning session
            (time(14, 0), time(17, 0))   # Afternoon session
        ]
        
        # Get existing appointments for this provider on this date
        existing_appointments = db.session.query(Appointment).filter(
            Appointment.doctor_id == provider['id'],
            func.date(Appointment.date) == appointment_date,
            Appointment.status.in_(['scheduled', 'confirmed'])
        ).all()
        
        # Convert to time blocks
        blocked_times = []
        for apt in existing_appointments:
            start = apt.date.time()
            end = (apt.date + timedelta(minutes=apt.duration_minutes or 30)).time()
            blocked_times.append((start, end))
        
        # Generate slots for each work session
        for session_start, session_end in work_hours:
            current_time = datetime.combine(appointment_date, session_start)
            session_end_dt = datetime.combine(appointment_date, session_end)
            
            while current_time + timedelta(minutes=duration_minutes) <= session_end_dt:
                slot_end = current_time + timedelta(minutes=duration_minutes)
                
                # Check if slot conflicts with existing appointments
                is_available = True
                for blocked_start, blocked_end in blocked_times:
                    blocked_start_dt = datetime.combine(appointment_date, blocked_start)
                    blocked_end_dt = datetime.combine(appointment_date, blocked_end)
                    
                    if (current_time < blocked_end_dt and slot_end > blocked_start_dt):
                        is_available = False
                        break
                
                if is_available:
                    slots.append(TimeSlot(
                        start_time=current_time,
                        end_time=slot_end,
                        provider_id=provider['id'],
                        department_id=provider['department_id'],
                        is_available=True,
                        buffer_time=self.buffer_time
                    ))
                
                # Move to next slot (including buffer time)
                current_time += timedelta(minutes=duration_minutes + self.buffer_time)
        
        return slots
    
    def _get_available_providers(
        self, 
        department_id: Optional[str],
        provider_id: Optional[str],
        appointment_type: str
    ) -> List[Dict]:
        """Get list of available providers"""
        
        query = db.session.query(Staff).filter(
            Staff.is_active == True,
            Staff.role.in_(['doctor', 'physician', 'specialist'])
        )
        
        if provider_id:
            query = query.filter(Staff.id == provider_id)
        elif department_id:
            query = query.filter(Staff.department_id == department_id)
        
        providers = query.all()
        
        return [
            {
                'id': p.id,
                'name': f"{p.first_name} {p.last_name}",
                'department_id': p.department_id,
                'specialization': p.specialization,
                'role': p.role
            } for p in providers
        ]
    
    def _get_patient_preferences(self, patient_id: str) -> SchedulingPreference:
        """Get patient scheduling preferences (would be stored in database)"""
        # For now, return default preferences
        # In reality, this would query a preferences table
        return SchedulingPreference(
            patient_id=patient_id,
            preferred_times=["morning", "afternoon"],
            preferred_days=[0, 1, 2, 3, 4],  # Weekdays
            max_wait_time=30
        )
    
    def create_appointment(
        self,
        patient_id: str,
        slot: TimeSlot,
        appointment_type: str = "consultation",
        reason: str = "",
        priority: AppointmentPriority = AppointmentPriority.ROUTINE,
        notes: str = ""
    ) -> Optional[str]:
        """Create a new appointment"""
        
        try:
            new_appointment = Appointment(
                id=str(uuid.uuid4()),
                client_id=patient_id,
                doctor_id=slot.provider_id,
                department_id=slot.department_id,
                date=slot.start_time,
                duration_minutes=int((slot.end_time - slot.start_time).total_seconds() / 60),
                appointment_type=appointment_type,
                status='scheduled',
                reason=reason,
                priority=priority.name.lower(),
                notes=notes,
                created_at=datetime.utcnow()
            )
            
            db.session.add(new_appointment)
            db.session.commit()
            
            # Send notifications (implement separately)
            self._send_appointment_confirmation(new_appointment)
            
            return new_appointment.id
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating appointment: {e}")
            return None
    
    def _send_appointment_confirmation(self, appointment: Appointment):
        """Send appointment confirmation (placeholder)"""
        # This would integrate with notification service
        print(f"Appointment confirmation sent for {appointment.id}")

class QueueManager:
    """Real-time queue management system"""
    
    def __init__(self):
        self.active_queues: Dict[str, List[QueueEntry]] = {}  # provider_id -> queue
        self.average_appointment_duration = 30  # minutes
    
    def add_to_queue(
        self, 
        patient_id: str, 
        appointment_id: str, 
        provider_id: str,
        priority: AppointmentPriority = AppointmentPriority.ROUTINE
    ) -> QueueEntry:
        """Add patient to queue"""
        
        queue_entry = QueueEntry(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            appointment_id=appointment_id,
            arrival_time=datetime.utcnow(),
            priority=priority,
            estimated_wait_time=0
        )
        
        # Initialize queue if it doesn't exist
        if provider_id not in self.active_queues:
            self.active_queues[provider_id] = []
        
        # Add to queue based on priority
        queue = self.active_queues[provider_id]
        if priority == AppointmentPriority.EMERGENCY:
            # Emergency goes to front
            queue.insert(0, queue_entry)
        elif priority == AppointmentPriority.URGENT:
            # Urgent goes after emergencies but before routine
            insert_pos = 0
            for i, entry in enumerate(queue):
                if entry.priority != AppointmentPriority.EMERGENCY:
                    insert_pos = i
                    break
            else:
                insert_pos = len(queue)
            queue.insert(insert_pos, queue_entry)
        else:
            # Routine goes to back
            queue.append(queue_entry)
        
        # Update queue positions and wait times
        self._update_queue_positions(provider_id)
        
        return queue_entry
    
    def _update_queue_positions(self, provider_id: str):
        """Update queue positions and estimated wait times"""
        if provider_id not in self.active_queues:
            return
        
        queue = self.active_queues[provider_id]
        cumulative_wait = 0
        
        for i, entry in enumerate(queue):
            entry.queue_position = i + 1
            entry.estimated_wait_time = cumulative_wait
            
            # Add estimated appointment duration for next patient
            if entry.priority == AppointmentPriority.EMERGENCY:
                cumulative_wait += 45  # Emergency appointments take longer
            elif entry.priority == AppointmentPriority.URGENT:
                cumulative_wait += 35
            else:
                cumulative_wait += self.average_appointment_duration
    
    def get_queue_status(self, provider_id: str) -> Dict[str, Any]:
        """Get current queue status for a provider"""
        if provider_id not in self.active_queues:
            return {
                'queue_length': 0,
                'average_wait_time': 0,
                'patients': []
            }
        
        queue = self.active_queues[provider_id]
        active_patients = [entry for entry in queue if entry.status == 'waiting']
        
        avg_wait = (sum(entry.estimated_wait_time for entry in active_patients) / 
                   len(active_patients)) if active_patients else 0
        
        return {
            'queue_length': len(active_patients),
            'average_wait_time': round(avg_wait),
            'patients': [
                {
                    'id': entry.id,
                    'patient_id': entry.patient_id,
                    'position': entry.queue_position,
                    'estimated_wait': entry.estimated_wait_time,
                    'priority': entry.priority.name,
                    'arrival_time': entry.arrival_time.isoformat()
                } for entry in active_patients
            ]
        }
    
    def call_next_patient(self, provider_id: str) -> Optional[QueueEntry]:
        """Call the next patient in queue"""
        if provider_id not in self.active_queues:
            return None
        
        queue = self.active_queues[provider_id]
        for entry in queue:
            if entry.status == 'waiting':
                entry.status = 'in_progress'
                entry.called_time = datetime.utcnow()
                self._update_queue_positions(provider_id)
                return entry
        
        return None
    
    def complete_appointment(self, provider_id: str, queue_entry_id: str):
        """Mark appointment as completed and remove from queue"""
        if provider_id not in self.active_queues:
            return
        
        queue = self.active_queues[provider_id]
        for i, entry in enumerate(queue):
            if entry.id == queue_entry_id:
                entry.status = 'completed'
                queue.pop(i)
                break
        
        self._update_queue_positions(provider_id)
    
    def get_patient_wait_time(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get wait time information for a specific patient"""
        for provider_id, queue in self.active_queues.items():
            for entry in queue:
                if entry.patient_id == patient_id and entry.status == 'waiting':
                    current_wait = (datetime.utcnow() - entry.arrival_time).total_seconds() / 60
                    return {
                        'current_wait_minutes': round(current_wait),
                        'estimated_remaining_minutes': max(0, entry.estimated_wait_time - current_wait),
                        'queue_position': entry.queue_position,
                        'provider_id': provider_id
                    }
        
        return None

# Global instances
scheduling_engine = SmartSchedulingEngine()
queue_manager = QueueManager()
