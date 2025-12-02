from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .ors_client import geocode_address, get_route
from .eld_logs import generate_daily_logs
from .eld_logs import generate_eld_sheets

from datetime import datetime

class TripPlanView(APIView):

    # Helper to check if two coordinates are very close
    def coords_are_same(self, c1, c2):
        return abs(c1["lat"] - c2["lat"]) < 0.0001 and abs(c1["lng"] - c2["lng"]) < 0.0001

    def post(self, request):
        current = request.data.get("currentLocation")
        pickup = request.data.get("pickupLocation")
        dropoff = request.data.get("dropoffLocation")
        cycle_used = request.data.get("cycleUsed")

        try:
            #  Geocode all 3 locations
            current_c = geocode_address(current)
            pickup_c = geocode_address(pickup)
            dropoff_c = geocode_address(dropoff)

            #  ROUTE LEG 1: current -> pickup
            if self.coords_are_same(current_c, pickup_c):
                route1 = {
                    "distance_meters": 0,
                    "duration_seconds": 0,
                    "geometry": [[current_c["lng"], current_c["lat"]]]
                }
            else:
                route1 = get_route([
                    [current_c["lng"], current_c["lat"]],
                    [pickup_c["lng"], pickup_c["lat"]],
                ])

            #  ROUTE LEG 2: pickup -> dropoff
            if self.coords_are_same(pickup_c, dropoff_c):
                route2 = {
                    "distance_meters": 0,
                    "duration_seconds": 0,
                    "geometry": [[pickup_c["lng"], pickup_c["lat"]]]
                }
            else:
                route2 = get_route([
                    [pickup_c["lng"], pickup_c["lat"]],
                    [dropoff_c["lng"], dropoff_c["lat"]],
                ])

            #  Combine legs
            total_distance = route1["distance_meters"] + route2["distance_meters"]
            total_duration = route1["duration_seconds"] + route2["duration_seconds"]
            combined_geometry = route1["geometry"] + route2["geometry"]

            # Inside TripPlanView.post, after total_distance and total_duration
            cycle_used = float(request.data.get("cycleUsed", 0))
            start_time = datetime.now()

            eld_logs = generate_eld_sheets(
                total_distance, 
                total_duration, 
                cycle_used, 
                start_time=start_time,
                route_geometry=combined_geometry
            )

            #  Return response
            return Response({
                "routeMap": {
                    "leg1": route1["geometry"],  # current -> pickup
                    "leg2": route2["geometry"],  # pickup -> dropoff
                    "distanceMiles": round(total_distance / 1609.34, 2),
                    "durationHours": round(total_duration / 3600, 2),
                    # "polyline": combined_geometry,
                },
                "geocoded": {
                    "current": current_c,
                    "pickup": pickup_c,
                    "dropoff": dropoff_c
                },
                "eldLogs": eld_logs
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
