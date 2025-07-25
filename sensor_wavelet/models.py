from django.db import models

class UserProfile(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    password = models.CharField(max_length=100)
    dob = models.DateField()
    state = models.CharField(max_length=100)
    status = models.BooleanField(default=False) 
    is_active = models.BooleanField(default=False) 

    def __str__(self):
        return self.name

class SignalData(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    csv_file = models.FileField(upload_to='dataset/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class PredictionHistory(models.Model):
    user_id = models.IntegerField()
    predicted_bpm = models.CharField(max_length=10)
    cwt_image_path = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)