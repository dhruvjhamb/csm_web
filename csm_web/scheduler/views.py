from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import logout as auth_logout

from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import api_view

from .models import Attendance, Course, Profile, Section, Spacetime, Override
from .serializers import (
    AttendanceSerializer,
    CourseSerializer,
    ProfileSerializer,
    SectionSerializer,
    SpacetimeSerializer,
    OverrideSerializer,
)
from .permissions import IsLeader, IsLeaderOrReadOnly, IsReadIfOwner


def login(request):
    return render(request, "scheduler/login.html")


def logout(request):
    auth_logout(request)
    return redirect(reverse("index"))


def index(request):
    return render(request, "scheduler/index.html", {"user": request.user})


# REST Framework API Views


class CourseList(generics.ListAPIView):
    """
    Responds to GET /courses with a list of all existing courses.
    """

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsLeaderOrReadOnly)


class CourseDetail(generics.RetrieveAPIView):
    """
    Responds to GET /courses/$NAME/ with the courses object associated with the given slug name.
    """

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsLeaderOrReadOnly)

    def get_object(self):
        return self.queryset.get(name__iexact=self.kwargs["name"])


class CourseSectionList(generics.ListAPIView):
    """
    Responds to GET /courses/$NAME/sections with a list of all sections associated with the course
    of the given slug name.
    """

    queryset = Course.objects.all()
    serializer_class = SectionSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsLeaderOrReadOnly)

    def get_queryset(self):
        return Section.objects.filter(course__name__iexact=self.kwargs["name"])


class UserProfileList(generics.ListAPIView):
    """
    Returns a list of profiles associated with the currently logged in user.
    """

    serializer_class = ProfileSerializer
    permission_classes = (IsReadIfOwner,)

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)


class UserProfileDetail(generics.RetrieveAPIView):
    """
    Returns details for the profile with profile_id = $ID, selectively gated by leadership,
    i.e. only the leader or user associated with the profile should be able to retrieve this.
    """

    serializer_class = ProfileSerializer
    permission_classes = (IsReadIfOwner, IsLeader)

    def get_queryset(self):
        return Profile.objects.filter(user__pk=self.request.query_params.get("pk", ""))


class SectionDetail(generics.RetrieveAPIView):
    """
    Responds to GET /sections/$ID with the corresponding section.
    """

    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsLeaderOrReadOnly)

    def get_object(self):
        return self.queryset.get(pk=self.request.query_params.get("pk", ""))

# API Stubs


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer


class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer


class SpacetimeViewSet(viewsets.ModelViewSet):
    queryset = Spacetime.objects.all()
    serializer_class = SpacetimeSerializer


class OverrideViewSet(viewsets.ModelViewSet):
    queryset = Override.objects.all()
    serializer_class = OverrideSerializer
