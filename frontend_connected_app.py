from __future__ import annotations

from typing import Optional

import streamlit as st

from backend_system import Bed, EmergencyTriageSystem, MedicalAction, Patient

TOTAL_BEDS = 15

st.set_page_config(
    page_title="Sistema de Triage",
    page_icon="",
    layout="wide",
)


class BedGridView:
    def __init__(self, beds: list[Bed]) -> None:
        self.beds = beds

    def render(self) -> None:
        st.subheader("Camas UCI")
        columns = st.columns(5)

        for index, bed in enumerate(self.beds):
            with columns[index % 5]:
                status_label = "Libre" if bed.is_free() else "Ocupada"
                patient_label = bed.patient.name if bed.patient else "Sin paciente"
                card_class = "bed-free" if bed.is_free() else "bed-busy"

                st.markdown(
                    f"""
                    <div class="bed-card {card_class}">
                        <h4>Cama {bed.bed_id}</h4>
                        <p><strong>Estado:</strong><br>{status_label}</p>
                        <p><strong>Paciente:</strong><br>{patient_label}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


class QueueView:
    def __init__(self, patients: list[Patient]) -> None:
        self.patients = patients

    def render(self) -> None:
        st.subheader("Cola de espera")

        if not self.patients:
            st.info("No hay pacientes en espera.")
            return

        for position, patient in enumerate(self.patients, start=1):
            st.markdown(
                f"""
                <div class="info-card">
                    <strong>{position}.</strong> {patient.name}<br>
                    <span>ID: {patient.patient_id} | Triage: {patient.triage_level}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


class ActionsView:
    def __init__(self, actions: list[MedicalAction]) -> None:
        self.actions = actions

    def render(self) -> None:
        st.subheader("Registro de acciones")

        if not self.actions:
            st.info("Todavía no hay acciones registradas.")
            return

        for action in reversed(self.actions):
            patient_label = action.patient_id if action.patient_id else "N/A"
            st.markdown(
                f"""
                <div class="info-card">
                    <strong>{action.timestamp}</strong><br>
                    {action.description}<br>
                    <span>Paciente: {patient_label}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


class PatientProfileView:
    def __init__(self, patient: Optional[Patient], history: list[str]) -> None:
        self.patient = patient
        self.history = history

    def render(self) -> None:
        st.subheader("Perfil del paciente")

        if self.patient is None:
            st.info("Selecciona un paciente para ver su información.")
            return

        left_column, right_column = st.columns(2)

        with left_column:
            st.markdown(f"**ID:** {self.patient.patient_id}")
            st.markdown(f"**Nombre:** {self.patient.name}")
            st.markdown(f"**Documento:** {self.patient.document}")
            st.markdown(f"**Edad:** {self.patient.age}")
            st.markdown(f"**Motivo de consulta:** {self.patient.reason}")

        with right_column:
            st.markdown(f"**Triage:** Nivel {self.patient.triage_level}")
            st.markdown(f"**Estado:** {self.patient.status}")

            bed_label = (
                f"Cama {self.patient.assigned_bed + 1}"
                if self.patient.assigned_bed is not None
                else "Sin asignar"
            )

            st.markdown(f"**Cama UCI:** {bed_label}")
            st.markdown(
                f"**Doctor asignado:** {self.patient.assigned_doctor or 'Sin asignar'}"
            )
            st.markdown(f"**Registro:** {self.patient.created_at}")

        st.markdown("### Historial de intervenciones")

        if not self.history:
            st.warning("Este paciente no tiene intervenciones registradas todavía.")
            return

        for step, intervention in enumerate(self.history, start=1):
            st.markdown(f"{step}. {intervention}")


class HospitalFrontendApp:
    def __init__(self) -> None:
        self.state = st.session_state
        self._initialize_state()

    def _initialize_state(self) -> None:
        if "system" not in self.state:
            self.state.system = EmergencyTriageSystem(total_beds=TOTAL_BEDS)

        if "selected_patient_id" not in self.state:
            self.state.selected_patient_id = None

    @property
    def system(self) -> EmergencyTriageSystem:
        return self.state.system

    def run(self) -> None:
        self._configure_page()
        self._render_header()
        self._render_sidebar()
        self._render_dashboard()

    def _configure_page(self) -> None:
        self._inject_styles()

    def _inject_styles(self) -> None:
        st.markdown(
            """
            <style>
                .main-title {
                    font-size: 2.2rem;
                    font-weight: 800;
                    margin-bottom: 0.2rem;
                    color: #ffffff;
                }

                .subtitle {
                    color: #cbd5e1;
                    margin-bottom: 1rem;
                }

                .bed-card {
                    border-radius: 18px;
                    padding: 18px;
                    margin-bottom: 14px;
                    min-height: 215px;
                    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.12);
                    color: #1f2937 !important;
                }

                .bed-card h4 {
                    color: #111827 !important;
                    font-size: 1.65rem;
                    font-weight: 800;
                    margin-bottom: 14px;
                }

                .bed-card p {
                    color: #374151 !important;
                    font-size: 1rem;
                    margin-bottom: 12px;
                    line-height: 1.6;
                }

                .bed-card strong {
                    color: #111827 !important;
                }

                .bed-free {
                    background: #eefaf1;
                    border: 1px solid #b7e4c7;
                }

                .bed-busy {
                    background: #fff1f2;
                    border: 1px solid #fecdd3;
                }

                .info-card {
                    background: rgba(255, 255, 255, 0.04);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 14px;
                    padding: 12px 14px;
                    margin-bottom: 10px;
                }

                .info-card span {
                    color: #cbd5e1;
                    font-size: 0.92rem;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

    def _render_header(self) -> None:
        st.markdown(
            '<div class="main-title">Sistema de Triage y Flujo de Urgencias</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="subtitle">Frontend en Streamlit conectado a un backend en Python orientado a objetos.</div>',
            unsafe_allow_html=True,
        )
        self._render_metrics()
        st.divider()

    def _render_metrics(self) -> None:
        beds = self.system.get_beds()
        available_beds = sum(1 for bed in beds if bed.is_free())
        occupied_beds = len(beds) - available_beds
        total_patients = len(self.system.get_all_patients())
        queue_size = len(self.system.get_waiting_queue_patients())

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Pacientes registrados", total_patients)
        col2.metric("Pacientes en espera", queue_size)
        col3.metric("Camas libres", available_beds)
        col4.metric("Camas ocupadas", occupied_beds)

    def _render_sidebar(self) -> None:
        st.sidebar.title("Gestión rápida")
        self._render_patient_registration_form()
        st.sidebar.divider()
        self._render_doctor_management_section()
        st.sidebar.divider()
        self._render_undo_section()

    def _render_patient_registration_form(self) -> None:
        st.sidebar.subheader("Registrar paciente")

        with st.sidebar.form("patient_form", clear_on_submit=True):
            name = st.text_input("Nombre")
            document = st.text_input("Documento")
            age = st.number_input("Edad", min_value=0, max_value=120, value=18)
            reason = st.text_area("Motivo de consulta")
            triage_level = st.selectbox("Nivel de triage", [1, 2, 3, 4, 5], index=3)
            submit = st.form_submit_button("Guardar paciente")

            if submit:
                self._register_patient(
                    name=name,
                    document=document,
                    age=int(age),
                    reason=reason,
                    triage_level=int(triage_level),
                )

    def _render_doctor_management_section(self) -> None:
        st.sidebar.subheader("Personal médico")

        with st.sidebar.form("doctor_form", clear_on_submit=True):
            doctor_name = st.text_input("Nombre del doctor")
            specialty = st.text_input("Especialidad")
            shift = st.selectbox("Turno", ["Mañana", "Tarde", "Noche"])
            add_doctor = st.form_submit_button("Agregar doctor")

            if add_doctor:
                self._add_doctor(doctor_name, specialty, shift)

        staff = self.system.get_all_staff()

        if staff:
            doctor_options = [doctor.name for doctor in staff]
            doctor_to_remove = st.sidebar.selectbox(
                "Eliminar doctor",
                options=["Selecciona un doctor"] + doctor_options,
            )

            if (
                st.sidebar.button("Quitar doctor")
                and doctor_to_remove != "Selecciona un doctor"
            ):
                self._remove_doctor(doctor_to_remove)

        st.sidebar.markdown("### Doctores en turno")
        for doctor in self.system.get_all_staff():
            st.sidebar.markdown(f"- {doctor.name} | {doctor.role} | {doctor.shift}")

    def _render_undo_section(self) -> None:
        st.sidebar.subheader("Deshacer acción")
        st.sidebar.write("Revierte la última acción registrada.")

        if st.sidebar.button("Deshacer última acción"):
            self._undo_last_action()

    def _render_dashboard(self) -> None:
        top_left, top_right = st.columns([1.3, 1])

        with top_left:
            BedGridView(self.system.get_beds()).render()

        with top_right:
            QueueView(self.system.get_waiting_queue_patients()).render()

        st.divider()

        bottom_left, bottom_right = st.columns([1, 1.2])

        with bottom_left:
            ActionsView(self.system.get_actions()).render()

        with bottom_right:
            self._render_patient_profile_section()

    def _render_patient_profile_section(self) -> None:
        all_patients = self.system.get_all_patients()

        patient = self._get_selected_patient()
        history = self.system.get_patient_history(patient.patient_id) if patient else []
        PatientProfileView(patient, history).render()

        if not all_patients:
            return

        st.markdown("### Gestión del paciente")

        patient_options = {
            f"{patient.name} - {patient.patient_id}": patient.patient_id
            for patient in all_patients
        }

        labels = list(patient_options.keys())

        default_index = 0
        if self.state.selected_patient_id is not None:
            for index, label in enumerate(labels):
                if patient_options[label] == self.state.selected_patient_id:
                    default_index = index
                    break

        selected_label = st.selectbox(
            "Selecciona un paciente",
            options=labels,
            index=default_index,
        )

        self.state.selected_patient_id = patient_options[selected_label]
        patient = self._get_selected_patient()

        if patient is None:
            return

        doctor_names = [doctor.name for doctor in self.system.get_all_staff()]
        selected_doctor = st.selectbox(
            "Asignar doctor",
            options=["Sin asignar"] + doctor_names,
            key=f"doctor_{patient.patient_id}",
        )

        intervention_text = st.text_input(
            "Nueva intervención",
            placeholder="Ejemplo: Triage inicial, Rayos X, Examen de sangre",
            key=f"intervention_{patient.patient_id}",
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button(
                "Guardar intervención",
                key=f"save_intervention_{patient.patient_id}",
            ):
                self._add_intervention(patient.patient_id, intervention_text)

        with col2:
            if st.button("Asignar doctor", key=f"assign_doctor_{patient.patient_id}"):
                doctor_value = None if selected_doctor == "Sin asignar" else selected_doctor
                self._assign_doctor(patient.patient_id, doctor_value)

        with col3:
            if st.button("Asignar cama UCI", key=f"assign_bed_{patient.patient_id}"):
                self._assign_bed(patient.patient_id)

        if st.button("Atender siguiente paciente de la cola"):
            self._attend_next_patient()

    def _register_patient(
        self,
        name: str,
        document: str,
        age: int,
        reason: str,
        triage_level: int,
    ) -> None:
        if not name.strip() or not document.strip() or not reason.strip():
            st.warning("Completa todos los campos del paciente.")
            return

        patient = self.system.register_patient(name, document, age, reason, triage_level)
        self.state.selected_patient_id = patient.patient_id
        st.success(f"Paciente {patient.name} registrado correctamente.")

    def _add_doctor(self, doctor_name: str, specialty: str, shift: str) -> None:
        if not doctor_name.strip() or not specialty.strip():
            st.warning("Completa el nombre y la especialidad del doctor.")
            return

        self.system.add_staff_member(doctor_name, specialty, shift)
        st.success("Doctor agregado correctamente.")

    def _remove_doctor(self, doctor_name: str) -> None:
        removed = self.system.remove_staff_member(doctor_name)

        if removed:
            st.success("Doctor eliminado del turno.")
        else:
            st.warning("No se encontró el doctor.")

    def _assign_doctor(self, patient_id: str, doctor_name: Optional[str]) -> None:
        assigned = self.system.assign_doctor_to_patient(patient_id, doctor_name)

        if assigned:
            st.success("Cambio de doctor realizado.")
        else:
            st.warning("No se encontró el paciente.")

    def _add_intervention(self, patient_id: str, intervention_text: str) -> None:
        if not intervention_text.strip():
            st.warning("Escribe una intervención antes de guardarla.")
            return

        added = self.system.add_patient_intervention(patient_id, intervention_text)

        if added:
            st.success("Intervención guardada correctamente.")
        else:
            st.warning("No se encontró el paciente.")

    def _assign_bed(self, patient_id: str) -> None:
        bed_index = self.system.assign_first_available_bed(patient_id)

        if bed_index is None:
            patient = self.system.get_patient(patient_id)

            if patient and patient.assigned_bed is not None:
                st.info("El paciente ya tiene una cama asignada.")
            else:
                st.error("No hay camas UCI disponibles en este momento.")
            return

        patient = self.system.get_patient(patient_id)
        patient_name = patient.name if patient else "Paciente"
        st.success(f"Se asignó la cama {bed_index + 1} al paciente {patient_name}.")

    def _attend_next_patient(self) -> None:
        patient = self.system.attend_next_patient()

        if patient is None:
            st.info("No hay pacientes en la cola de espera.")
            return

        self.state.selected_patient_id = patient.patient_id
        st.success(f"Ahora se atiende a {patient.name}.")

    def _undo_last_action(self) -> None:
        last_action = self.system.undo_action()

        if last_action is None:
            st.info("No hay acciones para deshacer.")
            return

        st.warning(f"Acción retirada del registro: {last_action.description}")

    def _get_selected_patient(self) -> Optional[Patient]:
        patient_id = self.state.selected_patient_id

        if patient_id is None:
            return None

        return self.system.get_patient(patient_id)


if __name__ == "__main__":
    app = HospitalFrontendApp()
    app.run()