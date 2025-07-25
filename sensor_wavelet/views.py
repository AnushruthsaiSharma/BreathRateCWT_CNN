from django.shortcuts import render, redirect
from .forms import RegisterForm, LoginForm, SignalUploadForm
from .models import UserProfile, SignalData, PredictionHistory
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.conf import settings
from .cnn_model import cwt_transform, train_model
from django.views.decorators.csrf import csrf_exempt
import pywt
import os
import io
import base64
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cv2
from tensorflow.keras.models import load_model
from datetime import datetime


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user_login')
    else:
        form = RegisterForm()
    return render(request, 'user_register.html', {'form': form})


def admin_login(request):
    if request.method == 'POST':
        admin_id = request.POST.get('admin_id')
        password = request.POST.get('password')
        if admin_id == 'admin' and password == 'admin123':
            request.session['admin_logged_in'] = True
            return redirect('admin_dashboard')
        return render(request, 'admin_login.html', {'error': 'Invalid credentials'})
    return render(request, 'admin_login.html')


def user_login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        try:
            user = UserProfile.objects.get(email=email, password=password)
            if not user.is_active:
                return render(request, 'user_login.html', {'error': 'Your account is not activated'})
            request.session['user_id'] = user.id
            return redirect('user_dashboard')
        except UserProfile.DoesNotExist:
            return render(request, 'user_login.html', {'error': 'Invalid login credentials'})
    return render(request, 'user_login.html')


def admin_dashboard(request):
    if not request.session.get('admin_logged_in'):
        return redirect('admin_login')
    return render(request, 'admin_dashboard.html')


def admin_logout(request):
    request.session.flush()
    return redirect('admin_login')

def view_all_users(request):
    if not request.session.get('admin_logged_in'):
        return redirect('admin_login')
    users = UserProfile.objects.all()
    return render(request, 'view_all_users.html', {'users': users})


@csrf_exempt
def toggle_user(request, user_id):
    if not request.session.get('admin_logged_in'):
        return redirect('admin_login')
    user = UserProfile.objects.get(id=user_id)
    user.is_active = not user.is_active
    user.save()
    return redirect('view_all_users')

def view_all_predictions(request):
    if not request.session.get('admin_logged_in'):
        return redirect('admin_login')
    predictions = PredictionHistory.objects.all().order_by('-uploaded_at')
    data = []
    for p in predictions:
        try:
            user = UserProfile.objects.get(id=p.user_id)
            data.append({
                'name': user.name,
                'email': user.email,
                'bpm': p.predicted_bpm,
                'cwt': p.cwt_image_path,
                'time': p.uploaded_at,
            })
        except:
            continue
    return render(request, 'view_all_predictions.html', {'data': data, 'MEDIA_URL': settings.MEDIA_URL})


def view_trained_models(request):
    if not request.session.get('admin_logged_in'):
        return redirect('admin_login')
    model_dir = os.path.join(settings.BASE_DIR, 'trained_model')
    models = [f for f in os.listdir(model_dir) if f.endswith('.h5')]
    return render(request, 'view_trained_models.html', {'models': models})


def index(request):
    return render(request, 'index.html')


def user_dashboard(request):
    if not request.session.get('user_id'):
        return redirect('user_login')
    return render(request, 'user_dashboard.html', {'name': request.session.get('user_name')})


def view_profile(request):
    if not request.session.get('user_id'):
        return redirect('user_login')
    user_id = request.session.get('user_id')
    profile = UserProfile.objects.get(id=user_id)
    return render(request, 'view_profile.html', {'profile': profile})
def user_register(request):
    error = None
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        dob = request.POST.get('dob')
        state = request.POST.get('state')
        if password != confirm_password:
            error = "Passwords do not match!"
        elif UserProfile.objects.filter(email=email).exists():
            error = "Email already registered!"
        else:
            user = UserProfile(name=name, email=email, phone=phone,
                               password=password, dob=dob, state=state)
            user.save()
            return redirect('user_login')
    return render(request, 'user_register.html', {'error': error})


def cwt_transform(signal):
    scales = np.arange(1, 128)
    coef, _ = pywt.cwt(signal, scales, 'morl')
    return coef


def view_history(request):
    if not request.session.get('user_id'):
        return redirect('user_login')
    history = PredictionHistory.objects.filter(user_id=request.session.get('user_id')).order_by('-uploaded_at')
    return render(request, 'view_history.html', {
        'history': history,
        'MEDIA_URL': settings.MEDIA_URL
    })


def predict_signal(request):
    prediction = None
    cwt_image = None
    signal_plot = None
    if request.method == 'POST' and request.FILES.get('signal_file'):
        try:
            uploaded_file = request.FILES['signal_file']
            filename = uploaded_file.name.lower()
            if filename.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
                signal = df['voltage'].values
                time = df['time_index'].values if 'time_index' in df.columns else np.arange(len(signal))
            elif filename.endswith('.txt'):
                lines = uploaded_file.read().decode().splitlines()
                signal = np.array([float(val) for val in lines if val.strip()])
                time = np.arange(len(signal))
            else:
                raise ValueError("Unsupported file format")

            signal_norm = (signal - np.mean(signal)) / np.std(signal)
            cwt_img = cwt_transform(signal_norm)
            resized = cv2.resize(cwt_img, (64, 64))
            X = np.array(resized).reshape(1, 64, 64, 1)

            model = load_model('trained_model/cnn_model.h5')
            classes = np.load('trained_model/label_classes.npy')
            pred = model.predict(X)
            prediction = str(classes[np.argmax(pred)])

            cwt_dir = os.path.join(settings.MEDIA_ROOT, 'cwt_history')
            os.makedirs(cwt_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"user{request.session.get('user_id')}_{timestamp}.png"
            cwt_path = os.path.join(cwt_dir, filename)

            plt.figure(figsize=(6, 3))
            plt.imshow(cwt_img, aspect='auto', cmap='jet')
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(cwt_path)
            plt.close()

            PredictionHistory.objects.create(
                user_id=request.session.get('user_id'),
                predicted_bpm=prediction,
                cwt_image_path=f"cwt_history/{filename}"
            )

            buf = io.BytesIO()
            plt.figure(figsize=(6, 3))
            plt.imshow(cwt_img, aspect='auto', cmap='jet')
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(buf, format='png')
            buf.seek(0)
            cwt_image = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()

            fig2, ax2 = plt.subplots()
            ax2.plot(time, signal, color='black')
            ax2.set_title("Original Voltage Signal")
            ax2.set_xlabel("Time Index")
            ax2.set_ylabel("Voltage")
            fig2.tight_layout()
            buf2 = io.BytesIO()
            plt.savefig(buf2, format='png')
            buf2.seek(0)
            signal_plot = base64.b64encode(buf2.read()).decode('utf-8')
            plt.close()

        except Exception as e:
            prediction = f"❌ Error: {str(e)}"

    return render(request, 'predict_signal.html', {
        'prediction': prediction,
        'cwt_image': cwt_image,
        'signal_plot': signal_plot
    })


def logout_view(request):
    request.session.flush()
    return redirect('user_login')


def admin_train_dataset(request):
    if not request.session.get('admin_logged_in'):
        return redirect('admin_login')

    message = ""
    accuracy = None
    if request.method == 'POST' and request.FILES.get('dataset'):
        try:
            dataset_file = request.FILES['dataset']
            dataset_path = os.path.join(settings.BASE_DIR, 'dataset', dataset_file.name)
            os.makedirs(os.path.dirname(dataset_path), exist_ok=True)

            with open(dataset_path, 'wb+') as dest:
                for chunk in dataset_file.chunks():
                    dest.write(chunk)

            accuracy = train_model(dataset_path)
            message = "✅ Model trained successfully!"
        except:
            pass

    return render(request, 'admin_train_dataset.html', {
        'message': message,
        'accuracy': round(accuracy * 100, 2) if accuracy else None
    })


def train_dataset_view(request):
    if not request.session.get('admin_logged_in'):
        return redirect('admin_login')

    message = ""
    if request.method == 'POST' and request.FILES['dataset']:
        dataset_file = request.FILES['dataset']
        dataset_path = os.path.join('dataset', dataset_file.name)

        with open(dataset_path, 'wb+') as dest:
            for chunk in dataset_file.chunks():
                dest.write(chunk)

        train_model(dataset_path)
        message = "Model trained successfully using uploaded dataset!"

    return render(request, 'admin_train_dataset.html', {'message': message})


def admin_upload_dataset(request):
    if not request.session.get('admin_logged_in'):
        return redirect('admin_login')

    message = ''
    percent_accuracy = None  # ✅ initialize it safely

    if request.method == 'POST' and request.FILES.get('dataset_file'):
        file = request.FILES['dataset_file']
        fs = FileSystemStorage(location='media/dataset')
        filename = fs.save(file.name, file)
        file_path = os.path.join(fs.location, filename)

        try:
            accuracy = train_model(file_path)  # returns like 0.88
            percent_accuracy = accuracy * 100
            message = f"✅ Model trained successfully! Accuracy: {percent_accuracy:.0f}%"
        except Exception as e:
            message = f"❌ Training failed: {str(e)}"

    return render(request, 'admin_upload_dataset.html', {
        'message': message,
        'accuracy': f"{percent_accuracy:.0f}" if percent_accuracy is not None else None,
    })


def upload_signal(request):
    if not request.session.get('user_id'):
        return redirect('user_login')

    if request.method == 'POST':
        form = SignalUploadForm(request.POST, request.FILES)
        if form.is_valid():
            signal_data = form.save(commit=False)
            signal_data.user_id = request.session['user_id']
            signal_data.save()
            return redirect('predict_result', signal_id=signal_data.id)
    else:
        form = SignalUploadForm()

    return render(request, 'upload_signal.html', {'form': form})


def predict_result(request, signal_id):
    if not request.session.get('user_id'):
        return redirect('user_login')

    try:
        signal = SignalData.objects.get(id=signal_id)
        file_path = signal.csv_file.path
        df = pd.read_csv(file_path)

        if isinstance(df['voltage'][0], str):
            voltage = np.array([float(v) for v in df['voltage'][0].split()])
        else:
            voltage = df['voltage'].values

        cwt_img = cwt_transform(voltage)
        resized = cv2.resize(cwt_img, (64, 64))
        input_img = resized.reshape(1, 64, 64, 1)

        model = load_model('trained_model/cnn_model.h5')
        prediction = model.predict(input_img)
        predicted_class = int(np.argmax(prediction))

        return render(request, 'prediction_result.html', {'class': predicted_class})

    except Exception as e:
        return render(request, 'prediction_result.html', {'class': 'Error: ' + str(e)})


def batch_predict_signals(request):
    folder = os.path.join(settings.MEDIA_ROOT, 'cwt_images')
    model = load_model('trained_model/cnn_model.h5')
    classes = np.load('trained_model/label_classes.npy')
    results = []

    for filename in os.listdir(folder):
        if filename.endswith('.txt'):
            path = os.path.join(folder, filename)
            try:
                signal = np.loadtxt(path)
                signal = (signal - np.mean(signal)) / np.std(signal)
                cwt_img = pywt.cwt(signal, np.arange(1, 128), 'morl')[0]
                resized = cv2.resize(cwt_img, (64, 64)).reshape(1, 64, 64, 1)
                pred = model.predict(resized)
                predicted_label = classes[np.argmax(pred)]
                results.append(f"{filename} → {predicted_label} bpm")
            except Exception as e:
                results.append(f"{filename} → Error: {str(e)}")

    return HttpResponse("<br>".join(results))
