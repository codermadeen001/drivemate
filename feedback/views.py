from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Feedback
from .serializers import FeedbackSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_feedback(request):
    try:
        car_id = request.data.get('car_id')
        rental_id = request.data.get('rental_id')
        comment = request.data.get('comment')

        if not all([car_id, rental_id, comment]):
            return Response({"success": False, "message": "All fields are required"}, status=400)

        feedback = Feedback.objects.create(
            user=request.user,  # Save the user from request
            car_id=car_id,
            rental_id=rental_id,
            comment=comment
        )

        serializer = FeedbackSerializer(feedback)
        return Response({"success": True, "message": "Feedback submitted", "data": serializer.data}, status=201)

    except Exception as e:
        return Response({"success": False, "message": f"Error submitting feedback: {str(e)}"}, status=500)





@api_view(['POST'])
@permission_classes([AllowAny])
#@permission_classes([IsAuthenticated])
def delete_feedback(request):
    try:
        feedback_id = request.data.get('feedbackId')

        if not feedback_id:
            return Response({"success": False, "message": "Feedback ID is required"}, status=400)

        feedback = Feedback.objects.filter(feedback_id=feedback_id)#, user=request.user)

        if not feedback.exists():
            return Response({"success": False, "message": "Feedback not found or you don't have permission to delete it"}, status=404)

        feedback.delete()

        return Response({"success": True, "message": "Feedback deleted successfully"}, status=200)

    except Exception as e:
        return Response({"success": False, "message": f"Error deleting feedback: {str(e)}"}, status=500)






@api_view(['POST'])
@permission_classes([IsAuthenticated])
def client_get_feedback(request):
    try:
        car_id = request.data.get('car_id')
        rental_id = request.data.get('rental_id')

        if not car_id or not rental_id:
            return Response({
                "success": False,
                "message": "Both 'car_id' and 'rental_id' are required."
            }, status=400)

        feedback_qs = Feedback.objects.filter(
            car_id=car_id, user=request.user
        ).order_by('-feedback_date')  # Newest first

        if not feedback_qs.exists():
            return Response({
                "success": False,
                "message": "No feedback found for the given Car ID and Rental ID."
            }, status=404)

        serializer = FeedbackSerializer(feedback_qs, many=True)
        return Response({
            "success": True,
            "message": "Feedback retrieved successfully.",
            "data": serializer.data
        }, status=200)

    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error fetching feedback: {str(e)}"
        }, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def retrieve_feedback(request):
    try:
        car_id = request.data.get('car_id')

        if not car_id:
            return Response({
                "success": False,
                "message": "'car_id' is required."
            }, status=400)

        feedback_qs = Feedback.objects.select_related('user').filter(
            car_id=car_id
        ).order_by('-feedback_date')  # Newest first

        if not feedback_qs.exists():
            return Response({
                "success": False,
                "message": "No feedback found for the given Car ID."
            }, status=404)

        serializer = FeedbackSerializer(feedback_qs, many=True)
        return Response({
            "success": True,
            "message": "Feedback retrieved successfully.",
            "data": serializer.data
        }, status=200)

    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error fetching feedback: {str(e)}"
        }, status=500)
