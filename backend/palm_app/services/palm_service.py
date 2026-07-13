import logging

from datetime import datetime



from sqlalchemy import func

from sqlalchemy.exc import IntegrityError



from ..models.palm import PalmProfile

from .storage_service import StorageService



logger = logging.getLogger(__name__)





class PalmService:

    def __init__(self, request):

        self.request = request

        self.db = request.dbsession

        self.storage = StorageService(request.registry.settings)



    def create_palm(self, data, images=None):

        try:

            image_urls = self._upload_images(images)



            plant_date = self._parse_datetime(data.get('plant_date'))

            last_harvest = self._parse_datetime(data.get('last_harvest'))



            palm = PalmProfile(

                palm_id=data['palm_id'],

                palm_code=data['palm_code'],

                plant_date=plant_date,

                donner_name=data.get('donner_name'),

                donner_phone_number=data.get('donner_phone_number'),

                harvest_amount=self._parse_float(data.get('harvest_amount')),

                last_harvest=last_harvest,

                age=self._parse_int(data.get('age')),

                images=image_urls,

                area=data.get('area'),

                section=data.get('section'),

            )



            self.db.add(palm)

            self.db.flush()

            return palm



        except IntegrityError:

            self.db.rollback()

            raise ValueError(f"Palm with code {data.get('palm_code')} already exists")



    def _upload_images(self, images):

        if not images:

            return []



        image_urls = []

        for image in images:

            url = self.storage.upload_image(image)

            if url:

                image_urls.append(url)

        return image_urls



    def search_palms(

        self,

        palm_code=None,

        donner_name=None,

        donner_phone=None,

        area=None,

        section=None,

        page=1,

        per_page=20,

    ):

        query = self.db.query(PalmProfile)



        if palm_code:

            query = query.filter(PalmProfile.palm_code.ilike(f'%{palm_code}%'))

        if donner_name:

            query = query.filter(PalmProfile.donner_name.ilike(f'%{donner_name}%'))

        if donner_phone:

            query = query.filter(

                PalmProfile.donner_phone_number.ilike(f'%{donner_phone}%')

            )

        if area:

            query = query.filter(PalmProfile.area.ilike(f'%{area}%'))

        if section:

            query = query.filter(PalmProfile.section.ilike(f'%{section}%'))



        total = query.count()

        palms = (

            query.order_by(PalmProfile.id.desc())

            .offset((page - 1) * per_page)

            .limit(per_page)

            .all()

        )



        return {

            'palms': palms,

            'total': total,

            'page': page,

            'per_page': per_page,

            'pages': (total + per_page - 1) // per_page if per_page else 0,

        }



    def get_palm_by_id(self, palm_id):

        return self.db.query(PalmProfile).filter(PalmProfile.id == palm_id).first()



    def get_statistics(self):

        stats = self.db.query(

            func.count(PalmProfile.id).label('total_palms'),

            func.sum(PalmProfile.harvest_amount).label('total_harvest'),

            func.avg(PalmProfile.age).label('avg_age'),

        ).first()



        areas = (

            self.db.query(

                PalmProfile.area,

                func.count(PalmProfile.id).label('count'),

            )

            .group_by(PalmProfile.area)

            .all()

        )



        return {

            'total_palms': stats.total_palms or 0,

            'total_harvest': float(stats.total_harvest or 0),

            'average_age': float(stats.avg_age or 0),

            'areas': [

                {'name': area[0] or 'Unknown', 'count': area[1]}

                for area in areas

            ],

        }



    def update_palm(self, palm_id, data, images=None):

        palm = self.get_palm_by_id(palm_id)

        if not palm:

            raise ValueError('Palm not found')



        updatable_fields = [

            'palm_id', 'palm_code', 'donner_name', 'donner_phone_number',

            'harvest_amount', 'age', 'area', 'section',

        ]



        for key in updatable_fields:

            if key in data and data[key] is not None:

                if key in ('harvest_amount',):

                    setattr(palm, key, self._parse_float(data[key]))

                elif key in ('age',):

                    setattr(palm, key, self._parse_int(data[key]))

                else:

                    setattr(palm, key, data[key])



        if 'plant_date' in data and data['plant_date']:

            palm.plant_date = self._parse_datetime(data['plant_date'])

        if 'last_harvest' in data:

            palm.last_harvest = self._parse_datetime(data['last_harvest'])



        if images:

            new_urls = self._upload_images(images)

            existing = palm.images or []

            palm.images = existing + new_urls



        palm.updated_at = datetime.utcnow()

        self.db.flush()

        return palm



    def delete_palm(self, palm_id):

        palm = self.get_palm_by_id(palm_id)

        if not palm:

            raise ValueError('Palm not found')



        if palm.images:

            for image_url in palm.images:

                self.storage.delete_image(image_url)



        self.db.delete(palm)

        self.db.flush()



    def generate_report(self, start_date=None, end_date=None, section=None):

        query = self.db.query(

            PalmProfile.section,

            func.count(PalmProfile.id).label('count'),

            func.sum(PalmProfile.harvest_amount).label('total_harvest'),

        )



        if start_date:

            query = query.filter(PalmProfile.plant_date >= self._parse_datetime(start_date))

        if end_date:

            query = query.filter(PalmProfile.plant_date <= self._parse_datetime(end_date))

        if section:

            query = query.filter(PalmProfile.section == section)



        report_data = query.group_by(PalmProfile.section).all()



        return [

            {

                'section': row[0] or 'Unknown',

                'count': row[1],

                'total_harvest': float(row[2] or 0),

            }

            for row in report_data

        ]



    @staticmethod

    def _parse_datetime(value):

        if not value:

            return None

        if isinstance(value, datetime):

            return value

        if isinstance(value, str):

            for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):

                try:

                    return datetime.strptime(value[:19] if 'T' in value else value, fmt)

                except ValueError:

                    continue

            try:

                return datetime.fromisoformat(value.replace('Z', '+00:00').split('+')[0])

            except ValueError:

                return None

        return None



    @staticmethod

    def _parse_float(value):

        if value is None or value == '':

            return None

        return float(value)



    @staticmethod

    def _parse_int(value):

        if value is None or value == '':

            return None

        return int(value)


