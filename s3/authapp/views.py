from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes

# Create your views here.
import pyotp
import json
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

import random

# Simulated OTP storage
otp_store = {}

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import random
import logging



User = get_user_model()
otp_store = {}  # Temporary store for OTPs

import requests
import random
import logging
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User

otp_store = {}

import random
import requests
import logging
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
import time

otp_store = {}  # Temporary OTP storage
@permission_classes([AllowAny])

class RequestOTPView(APIView):
    def post(self, request):
        whatsapp_number = request.data.get("whatsapp_number")
        org_id = 1  # Assuming org_id is provided in request

        if not whatsapp_number:
            return Response({"error": "WhatsApp number is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=whatsapp_number)
        except ObjectDoesNotExist:
            return Response(
                {"error": "User not found. Please register first."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Send message to webhook before OTP
        webhook_url = "https://backend.bitz-itc.com/api/whatsapp/webhook/"
        webhook_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "101592599705197",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "phone_number_id": "555567910973933"
                        },
                        "contacts": [{
                            "profile": {"name": user.get_full_name() or "WhatsApp User"},
                            "wa_id": whatsapp_number
                        }],
                        "messages": [{
                            "from": whatsapp_number,
                            "id": f"wamid.{random.randint(100000, 999999)}",
                            "timestamp": str(int(time.time())),
                            "text": {"body": "I am requesting for an OTP"},
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }

        try:
            webhook_response = requests.post(
                webhook_url, json=webhook_payload, headers={"Content-Type": "application/json"}
            )
            if webhook_response.status_code != 200:
                logging.error(f"Failed to notify webhook: {webhook_response.text}")
        except requests.RequestException as e:
            logging.error(f"Error sending webhook message: {e}")

        # Generate a 6-digit OTP
        otp = str(random.randint(100000, 999999))
        otp_store[whatsapp_number] = otp  # Store OTP temporarily

        # Construct the OTP message
        otp_message = f"Your OTP is: {otp}. It expires in 5 minutes."

        # Send OTP via WhatsApp API
        try:
            response = requests.post(
                "https://backend.bitz-itc.com/api/whatsapp/whatsapp/send/",
                json={
                    "recipient": whatsapp_number,
                    "message_type": "text",
                    "content": otp_message,
                },
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                return Response({"message": "OTP sent successfully!"}, status=status.HTTP_200_OK)
            else:
                logging.error(f"Failed to send OTP: {response.text}")
                return Response(
                    {"error": "Failed to send OTP. Please try again later."},
                    status=response.status_code,
                )

        except requests.RequestException as e:
            logging.error(f"Request error while sending OTP: {e}")
            return Response(
                {"error": "Failed to send OTP. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@permission_classes([AllowAny])
class VerifyOTPView(APIView):

    def post(self, request):
        whatsapp_number = request.data.get("whatsapp_number")
        otp = request.data.get("otp")

        # Check if OTP is correct
        if otp_store.get(whatsapp_number) == otp:
            user = User.objects.get(username=whatsapp_number)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            # Remove OTP after successful login
            del otp_store[whatsapp_number]

            return Response({
                "access": access_token,
                "refresh": str(refresh)
            }, status=status.HTTP_200_OK)

        return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist

@permission_classes([AllowAny])

class RegisterUserView(APIView):
    def post(self, request):
        whatsapp_number = request.data.get("whatsapp_number")
        name = request.data.get("name")
        password = request.data.get("password")

        if not whatsapp_number or not password:
            return Response({"error": "WhatsApp number and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user exists
        if User.objects.filter(username=whatsapp_number).exists():
            return Response({"error": "User already exists."}, status=status.HTTP_400_BAD_REQUEST)

        # Create a new user
        user = User.objects.create_user(username=whatsapp_number, password=password, first_name=name)
        return Response({"message": "User registered successfully!"}, status=status.HTTP_201_CREATED)
