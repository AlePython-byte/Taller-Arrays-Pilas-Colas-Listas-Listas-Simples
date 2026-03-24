from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Deque, Dict, List, Optional


@dataclass
class Patient:
    patient_id: str
    name: str
    document: str
    age: int
    reason: str
    triage_level: int
    condition: str
    status: str = field(init=False)
    assigned_bed: Optional[int] = None
    assigned_doctor: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def __post_init__(self) -> None:
        self.status = "En espera" if self.triage_level in (4, 5) else "Atención prioritaria"

    def __str__(self) -> str:
        return f"{self.patient_id} - {self.name} (Triage {self.triage_level})"


@dataclass
class Bed:
    bed_id: int
    patient: Optional[Patient] = None

    def is_free(self) -> bool:
        return self.patient is None


@dataclass
class MedicalAction:
    action_type: str
    description: str
    patient_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))


@dataclass
class StaffMember:
    name: str
    role: str
    shift: str


class InterventionNode:
    def __init__(self, procedure_name: str) -> None:
        self.procedure_name = procedure_name
        self.next: Optional[InterventionNode] = None


class InterventionHistory:
    def __init__(self) -> None:
        self.head: Optional[InterventionNode] = None

    def add_intervention(self, procedure_name: str) -> None:
        new_node = InterventionNode(procedure_name)

        if self.head is None:
            self.head = new_node
            return

        current = self.head
        while current.next is not None:
            current = current.next
        current.next = new_node

    def to_list(self) -> List[str]:
        procedures: List[str] = []
        current = self.head

        while current is not None:
            procedures.append(current.procedure_name)
            current = current.next

        return procedures

    def display_history(self) -> str:
        history = self.to_list()
        if not history:
            return "No interventions registered"
        return " -> ".join(history)


class ICUBedManager:
    def __init__(self, total_beds: int) -> None:
        self.beds = [Bed(bed_id=i + 1) for i in range(total_beds)]

    def assign_first_available_bed(self, patient: Patient) -> Optional[int]:
        for index, bed in enumerate(self.beds):
            if bed.is_free():
                bed.patient = patient
                return index
        return None

    def release_bed(self, index: int) -> bool:
        if 0 <= index < len(self.beds) and not self.beds[index].is_free():
            self.beds[index].patient = None
            return True
        return False

    def get_all_beds(self) -> List[Bed]:
        return self.beds


class WaitingQueue:
    def __init__(self) -> None:
        self.queue: Deque[str] = deque()

    def enqueue_patient(self, patient_id: str) -> None:
        self.queue.append(patient_id)

    def dequeue_patient(self) -> Optional[str]:
        if self.queue:
            return self.queue.popleft()
        return None

    def remove_patient(self, patient_id: str) -> None:
        self.queue = deque(item for item in self.queue if item != patient_id)

    def to_list(self) -> List[str]:
        return list(self.queue)

    def is_empty(self) -> bool:
        return len(self.queue) == 0


class UndoStack:
    def __init__(self) -> None:
        self.stack: List[MedicalAction] = []

    def push_action(self, action: MedicalAction) -> None:
        self.stack.append(action)

    def undo_last_action(self) -> Optional[MedicalAction]:
        if self.stack:
            return self.stack.pop()
        return None

    def get_actions(self) -> List[MedicalAction]:
        return self.stack


class StaffDirectory:
    def __init__(self) -> None:
        self.staff_members: List[StaffMember] = []

    def add_staff_member(self, name: str, role: str, shift: str) -> None:
        self.staff_members.append(StaffMember(name=name, role=role, shift=shift))

    def remove_staff_member(self, name: str) -> bool:
        for member in self.staff_members:
            if member.name.lower() == name.lower():
                self.staff_members.remove(member)
                return True
        return False

    def get_all_staff(self) -> List[StaffMember]:
        return self.staff_members


class EmergencyTriageSystem:
    def __init__(self, total_beds: int) -> None:
        self.bed_manager = ICUBedManager(total_beds)
        self.waiting_queue = WaitingQueue()
        self.undo_stack = UndoStack()
        self.staff_directory = StaffDirectory()
        self.patient_histories: Dict[str, InterventionHistory] = {}
        self.patients: Dict[str, Patient] = {}
        self.patient_sequence = 1
        self._seed_staff()

    def _seed_staff(self) -> None:
        self.staff_directory.add_staff_member("Dra. Laura Gómez", "Urgencias", "Mañana")
        self.staff_directory.add_staff_member("Dr. Andrés Ruiz", "Medicina Interna", "Tarde")
        self.staff_directory.add_staff_member("Dra. Sofía Paz", "Cuidados Intensivos", "Noche")

    def _next_patient_id(self) -> str:
        patient_id = f"P-{self.patient_sequence:03d}"
        self.patient_sequence += 1
        return patient_id

    def register_patient(
        self,
        name: str,
        document: str,
        age: int,
        reason: str,
        triage_level: int,
    ) -> Patient:
        patient = Patient(
            patient_id=self._next_patient_id(),
            name=name.strip(),
            document=document.strip(),
            age=age,
            reason=reason.strip(),
            triage_level=triage_level,
            condition=reason.strip(),
        )
        self.patients[patient.patient_id] = patient
        self.patient_histories[patient.patient_id] = InterventionHistory()
        self.patient_histories[patient.patient_id].add_intervention("Ingreso al sistema")
        self.patient_histories[patient.patient_id].add_intervention(
            f"Clasificación en triage nivel {triage_level}"
        )

        if triage_level in (4, 5):
            self.waiting_queue.enqueue_patient(patient.patient_id)
            description = f"Paciente {patient.name} agregado a la cola"
        else:
            description = f"Paciente {patient.name} marcado para atención prioritaria"

        self.undo_stack.push_action(
            MedicalAction(
                action_type="REGISTER_PATIENT",
                description=description,
                patient_id=patient.patient_id,
            )
        )
        return patient

    def add_staff_member(self, name: str, role: str, shift: str) -> None:
        self.staff_directory.add_staff_member(name.strip(), role.strip(), shift)
        self.undo_stack.push_action(
            MedicalAction(
                action_type="ADD_STAFF",
                description=f"Doctor {name.strip()} agregado al turno",
            )
        )

    def remove_staff_member(self, name: str) -> bool:
        removed = self.staff_directory.remove_staff_member(name)
        if removed:
            self.undo_stack.push_action(
                MedicalAction(
                    action_type="REMOVE_STAFF",
                    description=f"Doctor {name} retirado del turno",
                )
            )
        return removed

    def assign_doctor_to_patient(self, patient_id: str, doctor_name: Optional[str]) -> bool:
        patient = self.patients.get(patient_id)
        if patient is None:
            return False

        patient.assigned_doctor = doctor_name
        description = "Doctor asignado" if doctor_name else "Doctor removido"
        self.undo_stack.push_action(
            MedicalAction(
                action_type="ASSIGN_DOCTOR",
                description=f"{description} para {patient.name}",
                patient_id=patient.patient_id,
            )
        )
        return True

    def add_patient_intervention(self, patient_id: str, procedure_name: str) -> bool:
        history = self.patient_histories.get(patient_id)
        patient = self.patients.get(patient_id)
        if history is None or patient is None:
            return False

        history.add_intervention(procedure_name.strip())
        self.undo_stack.push_action(
            MedicalAction(
                action_type="ADD_INTERVENTION",
                description=f"Intervención '{procedure_name.strip()}' agregada a {patient.name}",
                patient_id=patient.patient_id,
            )
        )
        return True

    def assign_first_available_bed(self, patient_id: str) -> Optional[int]:
        patient = self.patients.get(patient_id)
        if patient is None or patient.assigned_bed is not None:
            return None

        bed_index = self.bed_manager.assign_first_available_bed(patient)
        if bed_index is None:
            return None

        patient.assigned_bed = bed_index
        patient.status = "En cama UCI"
        self.waiting_queue.remove_patient(patient.patient_id)
        self.undo_stack.push_action(
            MedicalAction(
                action_type="ASSIGN_BED",
                description=f"Paciente {patient.name} asignado a cama {bed_index + 1}",
                patient_id=patient.patient_id,
            )
        )
        return bed_index

    def attend_next_patient(self) -> Optional[Patient]:
        next_patient_id = self.waiting_queue.dequeue_patient()
        if next_patient_id is None:
            return None

        patient = self.patients.get(next_patient_id)
        if patient is None:
            return None

        patient.status = "En atención"
        self.undo_stack.push_action(
            MedicalAction(
                action_type="CALL_PATIENT",
                description=f"Paciente {patient.name} llamado desde la cola",
                patient_id=patient.patient_id,
            )
        )
        return patient

    def get_patient_history(self, patient_id: str) -> List[str]:
        history = self.patient_histories.get(patient_id)
        if history is None:
            return []
        return history.to_list()

    def get_patient(self, patient_id: str) -> Optional[Patient]:
        return self.patients.get(patient_id)

    def get_all_patients(self) -> List[Patient]:
        return list(self.patients.values())

    def get_all_staff(self) -> List[StaffMember]:
        return self.staff_directory.get_all_staff()

    def get_beds(self) -> List[Bed]:
        return self.bed_manager.get_all_beds()

    def get_waiting_queue_patients(self) -> List[Patient]:
        return [self.patients[patient_id] for patient_id in self.waiting_queue.to_list() if patient_id in self.patients]

    def get_actions(self) -> List[MedicalAction]:
        return self.undo_stack.get_actions()

    def undo_action(self) -> Optional[MedicalAction]:
        return self.undo_stack.undo_last_action()
