
from parking.models import Vehicle


class VehicleRepository:
    @staticmethod
    def get_all():
        return Vehicle.objects.select_related("vehicle_type").all()

    @staticmethod
    def find_by_plate(plate):
        return Vehicle.objects.filter(
            plate__iexact=plate
        ).first()

    @staticmethod
    def create(**data):
        return Vehicle.objects.create(**data)

    @staticmethod
    def delete(vehicle):
        vehicle.delete()