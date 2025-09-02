import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth.models import User, Group
from hospital import models
from hospital.models import Doctor, Patient
from datetime import date
from hospital.views import is_admin, is_doctor, is_patient
from hospital.views import afterlogin_view
from django.test import RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.base import ContentFile

@pytest.fixture
def client():
    return Client()

@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(username='admin', password='adminpass')
    group, _ = Group.objects.get_or_create(name='ADMIN')
    group.user_set.add(user)
    return user

@pytest.fixture
def doctor_user(db):
    user = User.objects.create_user(username='doctor', password='doctorpass')
    group, _ = Group.objects.get_or_create(name='DOCTOR')
    group.user_set.add(user)
    doctor = models.Doctor.objects.create(user=user, status=True, mobile='123', address='abc', department='Cardiology')
    return user

@pytest.fixture
def patient_user(db, doctor_user):
    user = User.objects.create_user(username='patient', password='patientpass')
    group, _ = Group.objects.get_or_create(name='PATIENT')
    group.user_set.add(user)
    patient = models.Patient.objects.create(user=user, status=True, assignedDoctorId=doctor_user.id, mobile='456', address='def', symptoms='cough', admitDate=date.today())
    return user

def test_home_view_unauthenticated(client):
    response = client.get('/')
    assert response.status_code == 200
    assert 'hospital/index.html' in [t.name for t in response.templates]

def test_home_view_authenticated(client, admin_user):
    client.force_login(admin_user)
    response = client.get('/')
    assert response.status_code == 302
    assert response.url == 'afterlogin' 

def test_adminclick_view_unauthenticated(client):
    response = client.get('/adminclick')
    assert response.status_code == 200
    assert 'hospital/adminclick.html' in [t.name for t in response.templates]

def test_adminclick_view_authenticated(client, admin_user):
    client.force_login(admin_user)
    response = client.get('/adminclick')
    assert response.status_code == 302
    assert response.url == 'afterlogin'

def test_doctorclick_view_unauthenticated(client):
    response = client.get('/doctorclick')
    assert response.status_code == 200
    assert 'hospital/doctorclick.html' in [t.name for t in response.templates]

def test_doctorclick_view_authenticated(client, doctor_user):
    client.force_login(doctor_user)
    response = client.get('/doctorclick')
    assert response.status_code == 302
    assert response.url == 'afterlogin'

def test_patientclick_view_unauthenticated(client):
    response = client.get('/patientclick')
    assert response.status_code == 200
    assert 'hospital/patientclick.html' in [t.name for t in response.templates]

def test_patientclick_view_authenticated(client, patient_user):
    client.force_login(patient_user)
    response = client.get('/patientclick')
    assert response.status_code == 302
    assert response.url == 'afterlogin'

def test_admin_signup_view_get(client):
    response = client.get('/adminsignup')
    assert response.status_code == 200
    assert 'hospital/adminsignup.html' in [t.name for t in response.templates]
    assert 'form' in response.context

def test_admin_signup_view_post(client, db):
    data = {
        'username': 'newadmin',
        'password': 'newadminpass',
        'first_name': 'Admin',
        'last_name': 'User',
        'email': 'admin@example.com'
    }
    response = client.post('/adminsignup', data)
    assert response.status_code == 302
    assert response.url == 'adminlogin'

def test_doctor_signup_view_get(client):
    response = client.get('/doctorsignup')
    assert response.status_code == 200
    assert 'hospital/doctorsignup.html' in [t.name for t in response.templates]
    assert 'userForm' in response.context
    assert 'doctorForm' in response.context

def test_doctor_signup_view_post(client, db):
    data = {
        'username': 'newdoctor',
        'password': 'newdoctorpass',
        'first_name': 'Doctor',
        'last_name': 'User',
        'email': 'doctor@example.com',
        'mobile': '1234567890',
        'address': 'Doctor Address',
        'department': 'Cardiology'
    }
    response = client.post('/doctorsignup', data)
    assert response.status_code == 302
    assert response.url == 'doctorlogin'

@pytest.mark.django_db
def test_patient_signup_view_get(client):
    response = client.get('/patientsignup')
    assert response.status_code == 200
    assert 'hospital/patientsignup.html' in [t.name for t in response.templates]
    assert 'userForm' in response.context
    assert 'patientForm' in response.context

def test_patient_signup_view_post(client, db, doctor_user):
    data = {
        'username': 'newpatient',
        'password': 'newpatientpass',
        'first_name': 'Patient',
        'last_name': 'User',
        'email': 'patient@example.com',
        'mobile': '9876543210',
        'address': 'Patient Address',
        'symptoms': 'Cough',
        'assignedDoctorId': doctor_user.id
    }
    response = client.post('/patientsignup', data)
    assert response.status_code == 302
    assert response.url == 'patientlogin'

def test_is_admin(admin_user):
    assert is_admin(admin_user)

def test_is_doctor(doctor_user):
    assert is_doctor(doctor_user)

def test_is_patient(patient_user):
    assert is_patient(patient_user)

def test_is_admin_false(doctor_user):
    assert not is_admin(doctor_user)

def test_is_doctor_false(admin_user):
    assert not is_doctor(admin_user)

def test_is_patient_false(admin_user):
    assert not is_patient(admin_user)

@pytest.mark.django_db
def test_afterlogin_view_admin(admin_user):
    factory = RequestFactory()
    request = factory.get('/afterlogin')
    request.user = admin_user
    response = afterlogin_view(request)
    assert response.status_code == 302
    assert response.url == '/admin-dashboard'

@pytest.mark.django_db
def test_afterlogin_view_doctor(doctor_user):
    factory = RequestFactory()
    request = factory.get('/afterlogin')
    request.user = doctor_user
    response = afterlogin_view(request)
    assert response.status_code == 302
    assert response.url == '/doctor-dashboard'

@pytest.mark.django_db
def test_afterlogin_view_patient(patient_user):
    factory = RequestFactory()
    request = factory.get('/afterlogin')
    request.user = patient_user
    response = afterlogin_view(request)
    assert response.status_code == 302
    assert response.url == '/patient-dashboard'

@pytest.mark.django_db
def test_admin_dashboard_view(client, admin_user):
    client.force_login(admin_user)
    response = client.get('/admin-dashboard')
    assert response.status_code == 200
    assert 'hospital/admin_dashboard.html' in [t.name for t in response.templates]

    for key in ['doctors', 'patients', 'doctorcount', 'pendingdoctorcount', 'patientcount', 'pendingpatientcount', 'appointmentcount', 'pendingappointmentcount']:
        assert key in response.context

@pytest.mark.django_db
def test_admin_doctor_view(client, admin_user):
    client.force_login(admin_user)
    response = client.get('/admin-doctor')
    assert response.status_code == 200
    assert 'hospital/admin_doctor.html' in [t.name for t in response.templates]

@pytest.mark.django_db
def test_admin_view_doctor_view(client, admin_user):
    doctor_user = User.objects.create_user(username='doc1', password='pass123')
    Doctor.objects.create(
        user=doctor_user,
        profile_pic=SimpleUploadedFile(
            name='test_image.jpg',
            content=b'file_content',
            content_type='image/jpeg'
        )
    )
    
    client.force_login(admin_user)
    response = client.get('/admin-view-doctor')

    assert response.status_code == 200
    assert 'hospital/admin_view_doctor.html' in [t.name for t in response.templates]
    assert 'doctors' in response.context

def test_delete_doctor_from_hospital_view(client, admin_user, doctor_user):
    doctor = models.Doctor.objects.get(user=doctor_user)
    client.force_login(admin_user)
    response = client.get(f'/delete-doctor-from-hospital/{doctor.id}')
    assert response.status_code == 302
    assert response.url == '/admin-view-doctor'
    assert not models.Doctor.objects.filter(id=doctor.id).exists()
    assert not User.objects.filter(id=doctor_user.id).exists()

@pytest.mark.django_db
def test_update_doctor_view_get(client, admin_user, doctor_user):
    doctor = models.Doctor.objects.get(user=doctor_user)
    client.force_login(admin_user)
    response = client.get(f'/update-doctor/{doctor.id}')
    assert response.status_code == 200
    assert 'hospital/admin_update_doctor.html' in [t.name for t in response.templates]
    assert 'userForm' in response.context
    assert 'doctorForm' in response.context

@pytest.mark.django_db
def test_admin_add_doctor_view_get(client, admin_user):
    client.force_login(admin_user)
    response = client.get('/admin-add-doctor')
    assert response.status_code == 200
    assert 'hospital/admin_add_doctor.html' in [t.name for t in response.templates]
    assert 'userForm' in response.context
    assert 'doctorForm' in response.context


VALID_DEPARTMENT = models.Doctor._meta.get_field('department').choices[0][0]
@pytest.mark.django_db
def test_update_doctor_view_post(client, admin_user, doctor_user):
    doctor = models.Doctor.objects.get(user=doctor_user)
    client.force_login(admin_user)

    data = {
        'username': 'updateddoctor',
        'password': 'updatedpass',
        'first_name': 'Updated',
        'last_name': 'Doctor',
        'mobile': '9999999999',
        'address': 'Updated Address',
        'department': VALID_DEPARTMENT
    }

    files = {
        'profile_pic': SimpleUploadedFile(
            name='test_image.jpg',
            content=b'file_content',
            content_type='image/jpeg'
        )
    }

    response = client.post(f'/update-doctor/{doctor.id}', data=data, files=files)
    assert response.status_code == 302
    
    doctor.refresh_from_db()
    doctor_user.refresh_from_db()
    assert doctor.mobile == '9999999999'
    assert doctor.address == 'Updated Address'
    assert doctor.department == VALID_DEPARTMENT
    assert doctor_user.username == 'updateddoctor'


@pytest.mark.django_db
def test_admin_add_doctor_view_post(client, admin_user):
    client.force_login(admin_user)

    data = {
        'username': 'newdoctor2',
        'password': 'newdoctorpass2',
        'first_name': 'New',
        'last_name': 'Doctor2',
        'mobile': '8888888888',
        'address': 'New Address',
        'department': VALID_DEPARTMENT
    }

    files = {
        'profile_pic': SimpleUploadedFile(
            name='new_image.jpg',
            content=b'file_content',
            content_type='image/jpeg'
        )
    }

    response = client.post('/admin-add-doctor', data=data, files=files)
    assert response.status_code == 302
    
    # Confirm doctor created
    doctor_exists = models.Doctor.objects.filter(
        mobile='8888888888',
        address='New Address',
        department=VALID_DEPARTMENT
    ).exists()
    assert doctor_exists

@pytest.mark.django_db
def test_admin_approve_doctor_view(client, admin_user):
    doctor_user = User.objects.create_user(username='doc1', password='pass123')
    doctor = Doctor.objects.create(
        user=doctor_user,
        status=False,
        profile_pic=SimpleUploadedFile(
            name='test_image.jpg',
            content=b'file_content',
            content_type='image/jpeg'
        )
    )
    
    client.force_login(admin_user)
    response = client.get('/admin-approve-doctor')

    assert response.status_code == 200
    assert 'hospital/admin_approve_doctor.html' in [t.name for t in response.templates]
    assert 'doctors' in response.context
    assert doctor in response.context['doctors'] 

@pytest.mark.django_db
def test_approve_doctor_view(client, admin_user, doctor_user):
    doctor = models.Doctor.objects.get(user=doctor_user)
    doctor.status = False
    doctor.save()
    client.force_login(admin_user)
    response = client.get(f'/approve-doctor/{doctor.id}')
    assert response.status_code == 302
    assert response.url == '/admin-approve-doctor'
    doctor.refresh_from_db()
    assert doctor.status is True

@pytest.mark.django_db
def test_reject_doctor_view(client, admin_user, doctor_user):
    doctor = models.Doctor.objects.get(user=doctor_user)
    client.force_login(admin_user)
    response = client.get(f'/reject-doctor/{doctor.id}')
    assert response.status_code == 302
    assert response.url == '/admin-approve-doctor'
    assert not models.Doctor.objects.filter(id=doctor.id).exists()
    assert not User.objects.filter(id=doctor_user.id).exists()

@pytest.mark.django_db
def test_admin_view_doctor_specialisation_view(client, admin_user, doctor_user):
    client.force_login(admin_user)
    response = client.get('/admin-view-doctor-specialisation')
    assert response.status_code == 200
    assert 'hospital/admin_view_doctor_specialisation.html' in [t.name for t in response.templates]
    assert 'doctors' in response.context

@pytest.mark.django_db
def test_admin_patient_view(client, admin_user):
    client.force_login(admin_user)
    response = client.get('/admin-patient')
    assert response.status_code == 200
    assert 'hospital/admin_patient.html' in [t.name for t in response.templates]

@pytest.mark.django_db
def test_admin_view_patient_view(client, admin_user):
    patient_user = User.objects.create_user(
        username='patient1',
        password='patientpass',
        first_name='Patient',
        last_name='One',
        email='patient1@example.com'
    )

    patient = Patient.objects.create(
        user=patient_user,
        address='123 Test Street',
        mobile='1234567890',
        symptoms='Fever and Cold',
        status=True,
        profile_pic=SimpleUploadedFile(
            name='patient_image.jpg',
            content=b'file_content',
            content_type='image/jpeg'
        )
    )

    client.force_login(admin_user)
    response = client.get('/admin-view-patient')

    assert response.status_code == 200
    assert 'hospital/admin_view_patient.html' in [t.name for t in response.templates]
    assert 'patients' in response.context
    assert patient in response.context['patients']
    
@pytest.mark.django_db
def test_delete_patient_from_hospital_view(client, admin_user, patient_user):
    patient = models.Patient.objects.get(user=patient_user)
    client.force_login(admin_user)
    response = client.get(f'/delete-patient-from-hospital/{patient.id}')
    assert response.status_code == 302
    assert response.url == '/admin-view-patient'
    assert not models.Patient.objects.filter(id=patient.id).exists()
    assert not User.objects.filter(id=patient_user.id).exists()

@pytest.mark.django_db
def test_update_patient_view_get(client, admin_user, patient_user):
    patient = models.Patient.objects.get(user=patient_user)
    client.force_login(admin_user)
    response = client.get(f'/update-patient/{patient.id}')
    assert response.status_code == 200
    assert 'hospital/admin_update_patient.html' in [t.name for t in response.templates]
    assert 'userForm' in response.context
    assert 'patientForm' in response.context

@pytest.mark.django_db
def test_update_patient_view_post(client, admin_user, patient_user, doctor_user):
    patient = models.Patient.objects.get(user=patient_user)
    client.force_login(admin_user)
    data = {
        'username': 'updatedpatient',
        'password': 'updatedpass',
        'first_name': 'Updated',
        'last_name': 'Patient',
        'mobile': '1111111111',
        'address': 'Updated Address',
        'symptoms': 'Updated Symptoms',
        'assignedDoctorId': doctor_user.id
    }
    response = client.post(f'/update-patient/{patient.id}', data)
    assert response.status_code == 302
    assert response.url == '/admin-view-patient'
    updated_patient = models.Patient.objects.get(id=patient.id)
    assert updated_patient.mobile == '1111111111'
    assert updated_patient.address == 'Updated Address'
    assert updated_patient.symptoms == 'Updated Symptoms'
    assert updated_patient.assignedDoctorId == doctor_user.id

@pytest.mark.django_db
def test_admin_add_patient_view_get(client, admin_user):
    client.force_login(admin_user)
    response = client.get('/admin-add-patient')
    assert response.status_code == 200
    assert 'hospital/admin_add_patient.html' in [t.name for t in response.templates]
    assert 'userForm' in response.context
    assert 'patientForm' in response.context

@pytest.mark.django_db
def test_admin_add_patient_view_post(client, admin_user, doctor_user):
    client.force_login(admin_user)
    data = {
        'username': 'newpatient2',
        'password': 'newpatientpass2',
        'first_name': 'New',
        'last_name': 'Patient2',
        'mobile': '2222222222',
        'address': 'New Address',
        'symptoms': 'New Symptoms',
        'assignedDoctorId': doctor_user.id
    }
    response = client.post('/admin-add-patient', data)
    assert response.status_code == 302
    assert models.Patient.objects.filter(mobile='2222222222', address='New Address', symptoms='New Symptoms', assignedDoctorId=doctor_user.id).exists()

@pytest.mark.django_db
def test_admin_approve_patient_view(client, admin_user, patient_user):
    patient = models.Patient.objects.get(user=patient_user)
    patient.status = False
    patient.save()
    client.force_login(admin_user)
    response = client.get('/admin-approve-patient')
    assert response.status_code == 200
    assert 'hospital/admin_approve_patient.html' in [t.name for t in response.templates]
    assert 'patients' in response.context
    assert patient in response.context['patients']

@pytest.mark.django_db
def test_admin_approve_patient_view(client, admin_user):
    patient_user = User.objects.create_user(
        username='patient1',
        password='patientpass',
        first_name='Patient',
        last_name='One',
        email='patient1@example.com'
    )

    patient = Patient.objects.create(
        user=patient_user,
        address='123 Test Street',
        mobile='1234567890',
        symptoms='Fever and Cold',
        status=False
    )
    patient.profile_pic.save('patient_image.jpg', ContentFile(b'file_content'), save=True)

    client.force_login(admin_user)
    response = client.get(f'/approve-patient/{patient.id}')

    assert response.status_code == 302
    assert response.url == '/admin-approve-patient'
    patient.refresh_from_db()
    assert patient.status is True

@pytest.mark.django_db
def test_reject_patient_view(client, admin_user, patient_user):
    patient = models.Patient.objects.get(user=patient_user)
    client.force_login(admin_user)
    response = client.get(f'/reject-patient/{patient.id}')
    assert response.status_code == 302
    assert response.url == '/admin-approve-patient'
    assert not models.Patient.objects.filter(id=patient.id).exists()
    assert not User.objects.filter(id=patient_user.id).exists()

@pytest.mark.django_db
def test_admin_view_appointment_view(client, admin_user):
    doctor_user = User.objects.create_user(username='doc3', password='pass123')
    patient_user = User.objects.create_user(username='pat2', password='pass123')
    doctor = Doctor.objects.create(user=doctor_user, status=True, mobile='123', address='abc', department='Cardiologist')
    patient = Patient.objects.create(user=patient_user, assignedDoctorId=doctor_user.id, mobile='1234567890', address='Test Address', symptoms='Test Symptoms', status=True)
    models.Appointment.objects.create(patientId=patient_user.id, doctorId=doctor_user.id, patientName=patient_user.first_name, doctorName=doctor_user.first_name, description='Test appointment', status=True)
    client.force_login(admin_user)
    response = client.get('/admin-view-appointment')
    assert response.status_code == 200
    assert 'hospital/admin_view_appointment.html' in [t.name for t in response.templates]
    assert 'appointments' in response.context

@pytest.mark.django_db
def test_admin_discharge_patient_view(client, admin_user, patient_user):
    patient = models.Patient.objects.get(user=patient_user)
    patient.status = True
    patient.save()
    client.force_login(admin_user)
    response = client.get('/admin-discharge-patient')
    assert response.status_code == 200
    assert 'hospital/admin_discharge_patient.html' in [t.name for t in response.templates]
    assert 'patients' in response.context
    assert patient in response.context['patients']

@pytest.mark.django_db
def test_discharge_patient_view_get(client, admin_user, patient_user, doctor_user):
    patient = models.Patient.objects.get(user=patient_user)
    patient.status = True
    patient.save()
    client.force_login(admin_user)
    response = client.get(f'/discharge-patient/{patient.id}')
    assert response.status_code == 200
    assert 'hospital/patient_generate_bill.html' in [t.name for t in response.templates]
    assert 'patientId' in response.context

@pytest.mark.django_db
def test_discharge_patient_view_post(client, admin_user, patient_user, doctor_user):
    patient = models.Patient.objects.get(user=patient_user)
    patient.status = True
    patient.save()
    client.force_login(admin_user)
    data = {
        'roomCharge': '100',
        'doctorFee': '200',
        'medicineCost': '50',
        'OtherCharge': '30'
    }
    response = client.post(f'/discharge-patient/{patient.id}', data)
    assert response.status_code == 200
    assert 'hospital/patient_final_bill.html' in [t.name for t in response.templates]
    assert 'total' in response.context

@pytest.mark.django_db
def test_render_to_pdf_and_download_pdf_view(client, admin_user, patient_user, doctor_user):

    patient = models.Patient.objects.get(user=patient_user)
    discharge = models.PatientDischargeDetails.objects.create(
        patientId=patient.id,
        patientName='Test Patient',
        assignedDoctorName='Test Doctor',
        address='Test Address',
        mobile='1234567890',
        symptoms='Test Symptoms',
        admitDate=date.today(),
        releaseDate=date.today(),
        daySpent=2,
        roomCharge=100,
        medicineCost=50,
        doctorFee=200,
        OtherCharge=30,
        total=380
    )
    client.force_login(admin_user)
    response = client.get(f'/download-pdf/{patient.id}')
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'

@pytest.mark.django_db
def test_admin_appointment_view(client, admin_user):
    client.force_login(admin_user)
    response = client.get('/admin-appointment')
    assert response.status_code == 200
    assert 'hospital/admin_appointment.html' in [t.name for t in response.templates]

@pytest.mark.django_db
def test_admin_add_appointment_view_get(client, admin_user):
    client.force_login(admin_user)
    response = client.get('/admin-add-appointment')
    assert response.status_code == 200
    assert 'hospital/admin_add_appointment.html' in [t.name for t in response.templates]
    assert 'appointmentForm' in response.context

@pytest.mark.django_db
def test_admin_add_appointment_view_post(client, admin_user, doctor_user, patient_user):
    client.force_login(admin_user)
    data = {
        'doctorId': doctor_user.id,
        'patientId': patient_user.id,
        'description': 'Test appointment',
        'appointmentDate': date.today()
    }
    response = client.post('/admin-add-appointment', data)
    assert response.status_code == 302
    assert models.Appointment.objects.filter(doctorId=doctor_user.id, patientId=patient_user.id, description='Test appointment').exists()

@pytest.mark.django_db
def test_admin_approve_appointment_view(client, admin_user, doctor_user, patient_user):
    appointment = models.Appointment.objects.create(doctorId=doctor_user.id, patientId=patient_user.id, doctorName='Doc', patientName='Pat', description='Test', status=False)
    client.force_login(admin_user)
    response = client.get('/admin-approve-appointment')
    assert response.status_code == 200
    assert 'hospital/admin_approve_appointment.html' in [t.name for t in response.templates]
    assert 'appointments' in response.context
    assert appointment in response.context['appointments']

@pytest.mark.django_db
def test_approve_appointment_view(client, admin_user, doctor_user, patient_user):
    appointment = models.Appointment.objects.create(doctorId=doctor_user.id, patientId=patient_user.id, doctorName='Doc', patientName='Pat', description='Test', status=False)
    client.force_login(admin_user)
    response = client.get(f'/approve-appointment/{appointment.id}')
    assert response.status_code == 302
    assert response.url == '/admin-approve-appointment'
    appointment.refresh_from_db()
    assert appointment.status is True

@pytest.mark.django_db
def test_reject_appointment_view(client, admin_user, doctor_user, patient_user):
    appointment = models.Appointment.objects.create(doctorId=doctor_user.id, patientId=patient_user.id, doctorName='Doc', patientName='Pat', description='Test', status=False)
    client.force_login(admin_user)
    response = client.get(f'/reject-appointment/{appointment.id}')
    assert response.status_code == 302
    assert response.url == '/admin-approve-appointment'
    assert not models.Appointment.objects.filter(id=appointment.id).exists()

@pytest.mark.django_db
def test_doctor_dashboard_view(client, doctor_user, patient_user):
    doctor = models.Doctor.objects.get(user=doctor_user)
    doctor.profile_pic = SimpleUploadedFile(
        name='doc_image.jpg',
        content=b'file_content',
        content_type='image/jpeg'
    )
    
    doctor.save()
    patient = models.Patient.objects.get(user=patient_user)
    patient.profile_pic = SimpleUploadedFile(
        name='patient_image.jpg',
        content=b'file_content',
        content_type='image/jpeg'
    )
    patient.assignedDoctorId = doctor.id
    patient.status = True
    patient.save()

    models.Appointment.objects.create(
        doctorId=doctor.id,
        patientId=patient_user.id,
        doctorName='Doc',
        patientName='Pat',
        description='Test',
        status=True
    )

    client.force_login(doctor_user)
    response = client.get('/doctor-dashboard')
    
    assert response.status_code == 200
    assert 'hospital/doctor_dashboard.html' in [t.name for t in response.templates]
    assert 'doctor' in response.context
    assert 'patientcount' in response.context
    assert 'appointmentcount' in response.context
    assert 'patientdischarged' in response.context


@pytest.mark.django_db
def test_doctor_patient_view(client, doctor_user):
    doctor = models.Doctor.objects.get(user=doctor_user)
    doctor.profile_pic.save('doc_image.jpg', ContentFile(b'file_content'), save=True)

    client.force_login(doctor_user)
    response = client.get('/doctor-patient')

    assert response.status_code == 200
    assert 'hospital/doctor_patient.html' in [t.name for t in response.templates]
    assert 'doctor' in response.context

@pytest.mark.django_db
def test_doctor_view_patient_view(client, doctor_user, patient_user):
    doctor = models.Doctor.objects.get(user=doctor_user)
    doctor.profile_pic = SimpleUploadedFile(
        name='doctor_image.jpg',
        content=b'file_content',
        content_type='image/jpeg'
    )
    doctor.save()

    patient = models.Patient.objects.get(user=patient_user)
    patient.profile_pic = SimpleUploadedFile(
        name='patient_image.jpg',
        content=b'file_content',
        content_type='image/jpeg'
    )
    patient.save()

    client.force_login(doctor_user)
    response = client.get('/doctor-view-patient')

    assert response.status_code == 200
    assert 'hospital/doctor_view_patient.html' in [t.name for t in response.templates]
    assert 'patients' in response.context


@pytest.mark.django_db
def test_search_view(client, doctor_user, patient_user):
    doctor = models.Doctor.objects.get(user=doctor_user)
    doctor.profile_pic = SimpleUploadedFile(
        name='doctor_image.jpg',
        content=b'file_content',
        content_type='image/jpeg'
    )
    doctor.save()

    patient = models.Patient.objects.get(user=patient_user)
    patient.profile_pic = SimpleUploadedFile(
        name='patient_image.jpg',
        content=b'file_content',
        content_type='image/jpeg'
    )
    patient.symptoms = 'cough'
    patient.save()

    client.force_login(doctor_user)
    response = client.get('/search', {'query': 'cough'})

    assert response.status_code == 200
    assert 'hospital/doctor_view_patient.html' in [t.name for t in response.templates]
    assert 'patients' in response.context


@pytest.mark.django_db
def test_doctor_view_discharge_patient_view(client, doctor_user, patient_user):
    doctor = models.Doctor.objects.get(user=doctor_user)
    doctor.profile_pic = SimpleUploadedFile(
        name='doctor_image.jpg',
        content=b'file_content',
        content_type='image/jpeg'
    )
    doctor.save()

    patient = models.Patient.objects.get(user=patient_user)
    patient.profile_pic = SimpleUploadedFile(
        name='patient_image.jpg',
        content=b'file_content',
        content_type='image/jpeg'
    )
    patient.status = False  # discharged
    patient.save()

    client.force_login(doctor_user)
    response = client.get('/doctor-view-discharge-patient')

    assert response.status_code == 200
    assert 'hospital/doctor_view_discharge_patient.html' in [t.name for t in response.templates]
    assert 'dischargedpatients' in response.context


@pytest.mark.django_db
def test_doctor_appointment_view(client, doctor_user):
    doctor = models.Doctor.objects.get(user=doctor_user)
    doctor.profile_pic = SimpleUploadedFile(
        name='doctor_image.jpg',
        content=b'file_content',
        content_type='image/jpeg'
    )
    doctor.save()

    client.force_login(doctor_user)
    response = client.get('/doctor-appointment')

    assert response.status_code == 200
    assert 'hospital/doctor_appointment.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_doctor_view_appointment_view(client, doctor_user):
    doctor = models.Doctor.objects.get(user=doctor_user)
    doctor.profile_pic = SimpleUploadedFile(
        name='doctor_image.jpg',
        content=b'file_content',
        content_type='image/jpeg'
    )
    doctor.save()

    client.force_login(doctor_user)
    response = client.get('/doctor-view-appointment')

    assert response.status_code == 200
    assert 'hospital/doctor_view_appointment.html' in [t.name for t in response.templates]
    assert 'appointments' in response.context


@pytest.mark.django_db
def test_doctor_delete_appointment_view(client, doctor_user):
    doctor = models.Doctor.objects.get(user=doctor_user)
    doctor.profile_pic = SimpleUploadedFile(
        name='doctor_image.jpg',
        content=b'file_content',
        content_type='image/jpeg'
    )
    doctor.save()

    client.force_login(doctor_user)
    response = client.get('/doctor-delete-appointment')

    assert response.status_code == 200 
    assert 'hospital/doctor_delete_appointment.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_delete_appointment_view(client, doctor_user, patient_user):
    doctor = models.Doctor.objects.get(user=doctor_user)
    doctor.profile_pic = SimpleUploadedFile(
        name='doctor_image.jpg',
        content=b'file_content',
        content_type='image/jpeg'
    )
    doctor.save()

    patient = models.Patient.objects.get(user=patient_user)
    patient.profile_pic = SimpleUploadedFile(
        name='patient_image.jpg',
        content=b'file_content',
        content_type='image/jpeg'
    )
    patient.status = True
    patient.save()

    appointment = models.Appointment.objects.create(
        patientId=patient.user.id,
        doctorId=doctor.user.id,
        patientName='Patient User',
        doctorName='Doctor User',
        description='Test Appointment',
        status=True
    )

    client.force_login(doctor_user)
    response = client.get(f'/delete-appointment/{appointment.id}')
    assert response.status_code == 200
    assert not models.Appointment.objects.filter(id=appointment.id).exists()


@pytest.mark.django_db
def test_patient_dashboard_view(client, patient_user):
    patient = models.Patient.objects.get(user=patient_user)
    patient.profile_pic = SimpleUploadedFile(
        name='patient_image.jpg', content=b'file_content', content_type='image/jpeg'
    )
    patient.save()

    client.force_login(patient_user)
    response = client.get(reverse('patient-dashboard'))

    assert response.status_code == 200
    assert 'hospital/patient_dashboard.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_patient_appointment_view(client, patient_user):
    patient = models.Patient.objects.get(user=patient_user)
    patient.profile_pic = SimpleUploadedFile(
        name='patient_image.jpg', content=b'file_content', content_type='image/jpeg'
    )
    patient.save()

    client.force_login(patient_user)
    response = client.get(reverse('patient-appointment'))

    assert response.status_code == 200
    assert 'hospital/patient_appointment.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_patient_book_appointment_view_get(client, patient_user):
    patient = models.Patient.objects.get(user=patient_user)
    patient.profile_pic = SimpleUploadedFile(
        name='patient_image.jpg', content=b'file_content', content_type='image/jpeg'
    )
    patient.save()

    client.force_login(patient_user)
    response = client.get(reverse('patient-book-appointment'))

    assert response.status_code == 200
    assert 'hospital/patient_book_appointment.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_patient_book_appointment_view_post(client, patient_user, doctor_user):
    patient = models.Patient.objects.get(user=patient_user)
    patient.profile_pic = SimpleUploadedFile(
        name='patient_image.jpg', content=b'file_content', content_type='image/jpeg'
    )
    patient.save()

    client.force_login(patient_user)
    data = {
        'doctorId': doctor_user.id,
        'description': 'Test appointment',
    }
    response = client.post(reverse('patient-book-appointment'), data)
    assert response.status_code == 302


@pytest.mark.django_db
def test_patient_view_doctor_view(client, patient_user, doctor_user):
    patient = models.Patient.objects.get(user=patient_user)
    patient.profile_pic = SimpleUploadedFile(
        name='patient_image.jpg',
        content=b'file_content',
        content_type='image/jpeg'
    )
    patient.save()

    doctor = models.Doctor.objects.get(user=doctor_user)
    doctor.profile_pic = SimpleUploadedFile(
        name='doctor_image.jpg',
        content=b'file_content',
        content_type='image/jpeg'
    )
    doctor.save()

    client.force_login(patient_user)
    response = client.get(reverse('patient-view-doctor'))

    assert response.status_code == 200
    assert 'hospital/patient_view_doctor.html' in [t.name for t in response.templates]
    assert 'patient' in response.context
    assert 'doctors' in response.context


@pytest.mark.django_db
def test_search_doctor_view(client, patient_user):
    patient = models.Patient.objects.get(user=patient_user)
    patient.profile_pic = SimpleUploadedFile(
        name='patient_image.jpg', content=b'file_content', content_type='image/jpeg'
    )
    patient.save()

    client.force_login(patient_user)
    response = client.get(reverse('searchdoctor'), {'query': 'Cardiologist'})

    assert response.status_code == 200
    assert 'hospital/patient_view_doctor.html' in [t.name for t in response.templates]
    assert 'patient' in response.context
    assert 'doctors' in response.context


@pytest.mark.django_db
def test_patient_view_appointment_view(client, patient_user):
    patient = models.Patient.objects.get(user=patient_user)
    patient.profile_pic = SimpleUploadedFile(
        name='patient_image.jpg', content=b'file_content', content_type='image/jpeg'
    )
    patient.save()

    client.force_login(patient_user)
    response = client.get(reverse('patient-view-appointment'))

    assert response.status_code == 200
    assert 'hospital/patient_view_appointment.html' in [t.name for t in response.templates]
    assert 'appointments' in response.context


@pytest.mark.django_db
def test_patient_discharge_view(client, patient_user):
    patient = models.Patient.objects.get(user=patient_user)
    patient.profile_pic = SimpleUploadedFile(
        name='patient_image.jpg', content=b'file_content', content_type='image/jpeg'
    )
    patient.status = False
    patient.save()

    client.force_login(patient_user)
    response = client.get(reverse('patient-discharge'))

    assert response.status_code == 200
    assert 'hospital/patient_discharge.html' in [t.name for t in response.templates]
    assert 'is_discharged' in response.context
    assert 'patient' in response.context



