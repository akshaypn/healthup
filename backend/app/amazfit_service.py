import requests
import json
import logging
import base64
import struct
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from . import models, schemas
from .amazfit_login import get_amazfit_token
from cryptography.fernet import Fernet
import os

logger = logging.getLogger(__name__)

class AmazfitService:
    """Service for interacting with real Huami/Zepp Amazfit API"""
    
    # Real Huami API endpoints
    USER_API_BASE = "https://api-user.huami.com"
    MIFIT_API_BASE = "https://api-mifit.huami.com"
    
    def __init__(self, app_token: str, user_id: str = None):
        self.app_token = app_token
        self.user_id = user_id
        self.session = requests.Session()
        
        # Set up headers exactly like the working script
        self.session.headers.update({
            'apptoken': app_token,
            'appname': 'com.xiaomi.hm.health',
            'appPlatform': 'web',
            'User-Agent': 'ZeppPython/1.7'  # Match the working script
        })
    
    @classmethod
    def from_credentials(cls, email: str, password: str):
        """Create service instance from email/password"""
        app_token, user_id = get_amazfit_token(email, password)
        return cls(app_token, user_id)
    
    @staticmethod
    def encrypt_credentials(email: str, password: str, key: bytes) -> tuple[str, str]:
        """Encrypt email and password"""
        f = Fernet(key)
        encrypted_email = f.encrypt(email.encode()).decode()
        encrypted_password = f.encrypt(password.encode()).decode()
        return encrypted_email, encrypted_password
    
    @staticmethod
    def decrypt_credentials(encrypted_email: str, encrypted_password: str, key: bytes) -> tuple[str, str]:
        """Decrypt email and password"""
        f = Fernet(key)
        email = f.decrypt(encrypted_email.encode()).decode()
        password = f.decrypt(encrypted_password.encode()).decode()
        return email, password
    
    def _make_request(self, url: str, method: str = 'GET', params: Dict = None, data: Dict = None) -> Dict:
        """Make API request to Huami/Zepp API"""
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, params=params, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Huami API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text}")
            raise Exception(f"Failed to communicate with Huami API: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Huami API response: {e}")
            raise Exception(f"Invalid response from Huami API: {str(e)}")
    
    def get_user_profile(self) -> Dict:
        """Get user profile information"""
        url = f"{self.USER_API_BASE}/v1/user/profile"
        return self._make_request(url)
    
    def get_heart_rate_data(self, target_date: date) -> List[int]:
        """Get heart rate data for specific date - returns list of BPM values (1440 values for 24 hours)"""
        if not self.user_id:
            raise Exception("User ID is required for heart rate data")
        
        url = f"{self.USER_API_BASE}/v1/user/fitness/heart_rate"
        params = {
            'userid': self.user_id,
            'date': target_date.strftime('%Y-%m-%d')
        }
        
        response = self._make_request(url, params=params)
        
        # Decode base64 heart rate data using the working logic from your script
        if 'heartRate' in response:
            blob = base64.b64decode(response['heartRate'])
            hr_values = []
            
            # Try different decoding approaches
            for off in range(0, len(blob), 2):
                if off + 1 < len(blob):
                    value = struct.unpack_from("<H", blob, off)[0]
                    
                    # Filter out invalid values (65535 is often used as "no data")
                    if value < 65535:
                        # Some devices might store HR in different ranges
                        if value > 300:  # If it's in the 300+ range, might need scaling
                            value = value // 10  # Scale down to get realistic BPM
                        hr_values.append(value)
                    else:
                        hr_values.append(0)  # No data
                else:
                    hr_values.append(0)
            
            return hr_values
        else:
            logger.warning(f"No heart rate data found for {target_date}")
            return []
    
    def get_activity_data(self, target_date: date) -> Dict:
        """Get activity data (steps, calories) for specific date"""
        if not self.user_id:
            raise Exception("User ID is required for activity data")
        
        url = f"{self.USER_API_BASE}/v1/user/fitness/activity"
        params = {
            'userid': self.user_id,
            'date': target_date.strftime('%Y-%m-%d')
        }
        
        return self._make_request(url, params=params)
    
    def get_sleep_data(self, target_date: date) -> Dict:
        """Get sleep data for specific date"""
        if not self.user_id:
            raise Exception("User ID is required for sleep data")
        
        url = f"{self.USER_API_BASE}/v1/user/fitness/sleep"
        params = {
            'userid': self.user_id,
            'date': target_date.strftime('%Y-%m-%d')
        }
        
        return self._make_request(url, params=params)
    
    def get_workout_history(self, limit: int = 200) -> List[Dict]:
        """Get workout history with pagination"""
        url = f"{self.MIFIT_API_BASE}/v1/sport/run/history.json"
        all_workouts = []
        next_track_id = None
        
        while True:
            params = {"source": "run.mifit.huami.com"}
            if next_track_id:
                params["stopTrackId"] = next_track_id
            
            response = self._make_request(url, params=params)
            
            if 'trackInfo' in response:
                all_workouts.extend(response['trackInfo'])
            
            # Check for next page
            next_track_id = response.get('next')
            if not next_track_id or len(all_workouts) >= limit:
                break
        
        return all_workouts[:limit]
    
    def get_workout_detail(self, track_id: str) -> Dict:
        """Get detailed workout data including GPS track"""
        url = f"{self.MIFIT_API_BASE}/v1/sport/run/detail.json"
        params = {
            'trackid': track_id,
            'source': 'run.mifit.huami.com'
        }
        
        return self._make_request(url, params=params)
    
    def get_band_data(self, target_date: date) -> Dict:
        """Get comprehensive band data for a specific date using the working script approach"""
        if not self.user_id:
            raise Exception("User ID is required for band data")
        
        url = f"{self.MIFIT_API_BASE}/v1/data/band_data.json"
        params = {
            "query_type": "detail",
            "userid": self.user_id,
            "device_type": "android_phone",
            "from_date": target_date.strftime('%Y-%m-%d'),
            "to_date": target_date.strftime('%Y-%m-%d')
        }
        
        # Use the exact same approach as the working script
        response = self.session.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    
    def decode_band_summary(self, band_data: Dict) -> Dict:
        """Decode base64-encoded JSON summary from band data - matches working script"""
        if not band_data or 'data' not in band_data or not band_data['data']:
            return {}
        
        try:
            # Get the summary from the first data entry
            summary_b64 = band_data['data'][0].get('summary', '')
            if summary_b64:
                # Use the exact same approach as the working script
                return json.loads(base64.b64decode(summary_b64 + "==").decode())
        except Exception as e:
            logger.error(f"Failed to decode band summary: {e}")
        
        return {}
    
    def get_daily_summary(self, target_date: date) -> Dict:
        """Get comprehensive daily summary including all metrics"""
        summary = {
            'date': target_date.strftime('%Y-%m-%d'),
            'heart_rate': [],
            'activity': {},
            'sleep': {},
            'workouts': [],
            'events': [],
            'hrv': 0,
            'hr_stats': {},
            'band_data': {}
        }
        
        try:
            # Get band data (includes summary, steps, sleep, etc.)
            band_data = self.get_band_data(target_date)
            summary['band_data'] = band_data
            
            # Decode the summary
            decoded_summary = self.decode_band_summary(band_data)
            
            # Extract activity data from decoded summary
            if 'stp' in decoded_summary:
                summary['activity'] = {
                    'steps': decoded_summary['stp'].get('ttl', 0),
                    'calories': decoded_summary['stp'].get('cal', 0),
                    'distance': decoded_summary['stp'].get('dis', 0),  # distance in meters
                    'active_minutes': decoded_summary['stp'].get('act', 0)  # active minutes
                }
            
            # Extract HRV data if available
            if 'hrv' in decoded_summary:
                summary['hrv'] = decoded_summary['hrv'].get('avg', 0)
            
            # Extract workout data if available
            if 'wkt' in decoded_summary:
                summary['workouts'] = decoded_summary['wkt']
            
            # Extract events data if available
            if 'evt' in decoded_summary:
                summary['events'] = decoded_summary['evt']
            
            # Extract sleep data from decoded summary
            if 'slp' in decoded_summary:
                slp = decoded_summary['slp']
                sleep_data = {}
                
                if 'st' in slp and 'ed' in slp:
                    # Convert UTC timestamps to IST (UTC+5:30)
                    from datetime import timezone, timedelta
                    ist_offset = timedelta(hours=5, minutes=30)
                    
                    # Convert sleep start and end times from UTC to IST
                    utc_start = datetime.fromtimestamp(slp['st'], tz=timezone.utc)
                    utc_end = datetime.fromtimestamp(slp['ed'], tz=timezone.utc)
                    
                    ist_start = utc_start + ist_offset
                    ist_end = utc_end + ist_offset
                    
                    # Calculate sleep duration in seconds
                    sleep_duration = slp['ed'] - slp['st']
                    sleep_data['sleep_time_seconds'] = sleep_duration
                    sleep_data['sleep_time_hours'] = sleep_duration / 3600
                    sleep_data['sleep_start'] = int(ist_start.timestamp())
                    sleep_data['sleep_end'] = int(ist_end.timestamp())
                    sleep_data['sleep_start_utc'] = slp['st']  # Keep original UTC for reference
                    sleep_data['sleep_end_utc'] = slp['ed']
                else:
                    # Fallback: try to find any numeric field that might be total sleep time
                    for key, value in slp.items():
                        if isinstance(value, (int, float)) and value > 0 and key not in ['st', 'ed']:
                            sleep_data['sleep_time_seconds'] = value
                            sleep_data['sleep_time_hours'] = value / 3600
                            break
                
                # Add detailed sleep stages if available
                if 'dp' in slp:
                    sleep_data['deep_sleep_minutes'] = slp['dp']
                    sleep_data['deep_sleep_hours'] = slp['dp'] / 60
                if 'lt' in slp:
                    sleep_data['light_sleep_minutes'] = slp['lt']
                    sleep_data['light_sleep_hours'] = slp['lt'] / 60
                if 'rm' in slp:
                    sleep_data['rem_sleep_minutes'] = slp['rm']
                    sleep_data['rem_sleep_hours'] = slp['rm'] / 60
                if 'wk' in slp:
                    sleep_data['awake_minutes'] = slp['wk']
                    sleep_data['awake_hours'] = slp['wk'] / 60
                
                summary['sleep'] = sleep_data
            
            # Get heart rate data from band data
            if band_data and 'data' in band_data and band_data['data']:
                print(f"DEBUG: Band data keys: {list(band_data.keys())}")
                print(f"DEBUG: Band data['data'] length: {len(band_data['data'])}")
                if band_data['data']:
                    print(f"DEBUG: First data entry keys: {list(band_data['data'][0].keys())}")
                    hr_blob = band_data['data'][0].get('data_hr', '')
                    print(f"DEBUG: HR blob length: {len(hr_blob)}")
                    if hr_blob:
                        decoded_hr = self.decode_hr_blob(hr_blob)
                        print(f"DEBUG: Decoded HR length: {len(decoded_hr)}")
                        print(f"DEBUG: Sample decoded HR: {decoded_hr[:10]}")
                        summary['heart_rate'] = decoded_hr
                        
                        # Calculate HR statistics
                        valid_hr = [hr for hr in decoded_hr if hr > 0]
                        if valid_hr:
                            summary['hr_stats'] = {
                                'avg_hr': sum(valid_hr) // len(valid_hr),
                                'max_hr': max(valid_hr),
                                'min_hr': min(valid_hr),
                                'duration_minutes': len(valid_hr),
                                'total_readings': len(decoded_hr),
                                'valid_readings': len(valid_hr)
                            }
                    else:
                        print("DEBUG: No HR blob found in band data")
                else:
                    print("DEBUG: No data entries in band_data")
            else:
                print("DEBUG: No band_data or no 'data' key")
            
        except Exception as e:
            logger.warning(f"Failed to get band data: {e}")
        
        # Fallback to individual API calls if band data fails
        if not summary['heart_rate']:
            try:
                summary['heart_rate'] = self.get_heart_rate_data(target_date)
            except Exception as e:
                logger.warning(f"Failed to get heart rate data: {e}")
        
        if not summary['activity']:
            try:
                summary['activity'] = self.get_activity_data(target_date)
            except Exception as e:
                logger.warning(f"Failed to get activity data: {e}")
        
        if not summary['sleep']:
            try:
                summary['sleep'] = self.get_sleep_data(target_date)
            except Exception as e:
                logger.warning(f"Failed to get sleep data: {e}")
        
        return summary
    
    def decode_hr_blob(self, hr_blob_b64: str) -> List[int]:
        """Decode heart rate blob from base64 string - 1 byte per minute, 30-240 BPM range"""
        try:
            raw = base64.b64decode(hr_blob_b64)
            hr_values = []
            
            # Each byte represents 1 minute of heart rate data
            for i in range(len(raw)):
                value = raw[i]
                
                # Filter valid BPM values (30-240 range as per Amazfit spec)
                if 30 <= value < 240:
                    hr_values.append(value)
                else:
                    hr_values.append(0)  # No data or invalid value
            
            return hr_values
        except Exception as e:
            logger.error(f"Failed to decode HR blob: {e}")
            return []

class AmazfitDataSync:
    """Service for syncing Amazfit data to local database using real Huami API"""
    
    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
        self.credentials = None
        self.amazfit_service = None
    
    def _get_credentials(self) -> Optional[models.AmazfitCredentials]:
        """Get user's Amazfit credentials"""
        if not self.credentials:
            self.credentials = self.db.query(models.AmazfitCredentials).filter(
                models.AmazfitCredentials.user_id == self.user_id
            ).first()
        return self.credentials
    
    def _init_service(self) -> AmazfitService:
        """Initialize Amazfit service with user credentials"""
        credentials = self._get_credentials()
        if not credentials:
            raise Exception("No Amazfit credentials found for user")
        
        if not self.amazfit_service:
            self.amazfit_service = AmazfitService(
                app_token=credentials.app_token,
                user_id=credentials.user_id_amazfit
            )
        
        return self.amazfit_service
    
    def _process_heart_rate_data(self, hr_values: List[int], target_date: date) -> Dict:
        """Process raw heart rate data into statistics"""
        if not hr_values:
            return {}
        
        # Filter out zero values (no data)
        valid_hr = [hr for hr in hr_values if hr > 0]
        
        if not valid_hr:
            return {}
        
        return {
            'avg_hr': sum(valid_hr) // len(valid_hr),
            'max_hr': max(valid_hr),
            'min_hr': min(valid_hr),
            'duration_minutes': len(valid_hr),
            'total_readings': len(hr_values),
            'valid_readings': len(valid_hr)
        }
    
    def _process_activity_data(self, activity_data: Dict) -> Dict:
        """Process activity data from Huami API"""
        if not activity_data:
            return {}
        
        # Extract relevant fields from Huami API response
        processed = {}
        
        # Handle both direct activity data and decoded summary data
        if isinstance(activity_data, dict):
            # Steps data from summary
            if 'steps' in activity_data:
                processed['steps'] = activity_data.get('steps', 0)
                processed['calories_burned'] = activity_data.get('calories', 0)
            elif 'summary' in activity_data:
                summary = activity_data['summary']
                processed['steps'] = summary.get('steps', 0)
                processed['calories_burned'] = summary.get('calories', 0)
                processed['distance_km'] = summary.get('distance', 0) / 1000  # Convert meters to km
                processed['active_minutes'] = summary.get('activeMinutes', 0)
            
            # Hourly steps if available
            if 'hourlySteps' in activity_data:
                processed['hourly_steps'] = activity_data['hourlySteps']
        
        return processed
    
    def _process_sleep_data(self, sleep_data: Dict) -> Dict:
        """Process sleep data from Huami API"""
        if not sleep_data:
            return {}
        
        processed = {}
        
        # Handle both direct sleep data and decoded summary data
        if isinstance(sleep_data, dict):
            # Sleep data from decoded summary
            if 'sleep_time_hours' in sleep_data:
                processed['sleep_hours'] = sleep_data.get('sleep_time_hours', 0)
                processed['sleep_time_seconds'] = sleep_data.get('sleep_time_seconds', 0)
                processed['sleep_start'] = sleep_data.get('sleep_start')
                processed['sleep_end'] = sleep_data.get('sleep_end')
            elif 'summary' in sleep_data:
                summary = sleep_data['summary']
                processed['sleep_hours'] = summary.get('sleepTime', 0) / 3600  # Convert seconds to hours
                processed['deep_sleep_hours'] = summary.get('deepSleepTime', 0) / 3600
                processed['light_sleep_hours'] = summary.get('lightSleepTime', 0) / 3600
                processed['rem_sleep_hours'] = summary.get('remSleepTime', 0) / 3600
                processed['awake_hours'] = summary.get('awakeTime', 0) / 3600
            
            # Sleep stages
            if 'sleepStages' in sleep_data:
                stages = sleep_data['sleepStages']
                # Process sleep stages if needed
                processed['sleep_stages'] = stages
        
        return processed
    
    def sync_activity_data(self, days_back: int = 7) -> int:
        """Sync activity data for the specified number of days"""
        service = self._init_service()
        synced_count = 0
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        try:
            current_date = start_date
            while current_date <= end_date:
                try:
                    # Get daily summary from Huami API using the working script approach
                    daily_summary = service.get_daily_summary(current_date)
                    
                    # Check if data already exists for this date
                    existing = self.db.query(models.ActivityData).filter(
                        models.ActivityData.user_id == self.user_id,
                        models.ActivityData.date == current_date
                    ).first()
                    
                    # Process activity data from decoded summary
                    activity_data = self._process_activity_data(daily_summary.get('activity', {}))
                    sleep_data = self._process_sleep_data(daily_summary.get('sleep', {}))
                    
                    # Process heart rate data
                    hr_stats = self._process_heart_rate_data(daily_summary.get('heart_rate', []), current_date)
                    
                    if existing:
                        # Update existing record
                        existing.calories_burned = activity_data.get('calories_burned', 0)
                        existing.active_minutes = activity_data.get('active_minutes', 0)
                        existing.distance_km = activity_data.get('distance_km', 0)
                        existing.steps = activity_data.get('steps', 0)
                        existing.sleep_hours = sleep_data.get('sleep_hours', 0)
                        existing.deep_sleep_hours = sleep_data.get('deep_sleep_hours', 0)
                        existing.light_sleep_hours = sleep_data.get('light_sleep_hours', 0)
                        existing.rem_sleep_hours = sleep_data.get('rem_sleep_hours', 0)
                        existing.awake_hours = sleep_data.get('awake_hours', 0)
                        existing.raw_data = daily_summary
                        existing.updated_at = datetime.utcnow()
                    else:
                        # Create new record
                        new_activity = models.ActivityData(
                            user_id=self.user_id,
                            date=current_date,
                            calories_burned=activity_data.get('calories_burned', 0),
                            active_minutes=activity_data.get('active_minutes', 0),
                            distance_km=activity_data.get('distance_km', 0),
                            steps=activity_data.get('steps', 0),
                            sleep_hours=sleep_data.get('sleep_hours', 0),
                            deep_sleep_hours=sleep_data.get('deep_sleep_hours', 0),
                            light_sleep_hours=sleep_data.get('light_sleep_hours', 0),
                            rem_sleep_hours=sleep_data.get('rem_sleep_hours', 0),
                            awake_hours=sleep_data.get('awake_hours', 0),
                            raw_data=daily_summary
                        )
                        self.db.add(new_activity)
                    
                    # Also sync heart rate data if available
                    if hr_stats:
                        self._sync_hr_session(current_date, hr_stats, daily_summary.get('heart_rate', []))
                    
                    synced_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to sync activity data for {current_date}: {e}")
                
                current_date += timedelta(days=1)
            
            self.db.commit()
            logger.info(f"Synced {synced_count} activity records for user {self.user_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to sync activity data: {e}")
            raise
        
        return synced_count
    
    def _sync_hr_session(self, target_date: date, hr_stats: Dict, hr_values: List[int]):
        """Sync heart rate session data"""
        if not hr_stats:
            return
        
        # Check if HR session already exists for this date
        existing = self.db.query(models.HRSession).filter(
            models.HRSession.user_id == self.user_id,
            models.HRSession.logged_at >= target_date,
            models.HRSession.logged_at < target_date + timedelta(days=1)
        ).first()
        
        if existing:
            # Update existing session
            existing.avg_hr = hr_stats.get('avg_hr')
            existing.max_hr = hr_stats.get('max_hr')
            existing.min_hr = hr_stats.get('min_hr')
            existing.duration_minutes = hr_stats.get('duration_minutes')
            existing.session_data = {
                'hr_values': hr_values,
                'stats': hr_stats
            }
        else:
            # Create new HR session
            new_hr = models.HRSession(
                user_id=self.user_id,
                avg_hr=hr_stats.get('avg_hr'),
                max_hr=hr_stats.get('max_hr'),
                min_hr=hr_stats.get('min_hr'),
                duration_minutes=hr_stats.get('duration_minutes'),
                session_data={
                    'hr_values': hr_values,
                    'stats': hr_stats
                },
                logged_at=datetime.combine(target_date, datetime.min.time())
            )
            self.db.add(new_hr)
    
    def sync_steps_data(self, days_back: int = 7) -> int:
        """Sync steps data for the specified number of days"""
        service = self._init_service()
        synced_count = 0
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        try:
            current_date = start_date
            while current_date <= end_date:
                try:
                    activity_data = service.get_activity_data(current_date)
                    processed_data = self._process_activity_data(activity_data)
                    
                    # Check if data already exists for this date
                    existing = self.db.query(models.StepsData).filter(
                        models.StepsData.user_id == self.user_id,
                        models.StepsData.date == current_date
                    ).first()
                    
                    if existing:
                        # Update existing record
                        existing.total_steps = processed_data.get('steps', 0)
                        existing.hourly_steps = processed_data.get('hourly_steps', [])
                        existing.calories_burned = processed_data.get('calories_burned', 0)
                        existing.distance_km = processed_data.get('distance_km', 0)
                        existing.active_minutes = processed_data.get('active_minutes', 0)
                        existing.raw_data = activity_data
                        existing.updated_at = datetime.utcnow()
                    else:
                        # Create new record
                        new_steps = models.StepsData(
                            user_id=self.user_id,
                            date=current_date,
                            total_steps=processed_data.get('steps', 0),
                            hourly_steps=processed_data.get('hourly_steps', []),
                            goal_steps=10000,  # Default goal
                            calories_burned=processed_data.get('calories_burned', 0),
                            distance_km=processed_data.get('distance_km', 0),
                            active_minutes=processed_data.get('active_minutes', 0),
                            raw_data=activity_data
                        )
                        self.db.add(new_steps)
                    
                    synced_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to sync steps data for {current_date}: {e}")
                
                current_date += timedelta(days=1)
            
            self.db.commit()
            logger.info(f"Synced {synced_count} steps records for user {self.user_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to sync steps data: {e}")
            raise
        
        return synced_count
    
    def sync_heart_rate_data(self, days_back: int = 7) -> int:
        """Sync heart rate data for the specified number of days"""
        service = self._init_service()
        synced_count = 0
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        try:
            current_date = start_date
            while current_date <= end_date:
                try:
                    hr_values = service.get_heart_rate_data(current_date)
                    hr_stats = self._process_heart_rate_data(hr_values, current_date)
                    
                    if hr_stats:
                        self._sync_hr_session(current_date, hr_stats, hr_values)
                        synced_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to sync HR data for {current_date}: {e}")
                
                current_date += timedelta(days=1)
            
            self.db.commit()
            logger.info(f"Synced {synced_count} HR records for user {self.user_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to sync HR data: {e}")
            raise
        
        return synced_count
    
    def sync_all_data(self, days_back: int = 7) -> Dict[str, int]:
        """Sync all data types using real Huami API"""
        results = {
            'activity_synced': 0,
            'steps_synced': 0,
            'heart_rate_synced': 0,
            'sleep_synced': 0
        }
        
        try:
            # Update last sync time
            credentials = self._get_credentials()
            if credentials:
                credentials.last_sync = datetime.utcnow()
                self.db.commit()
            
            # Sync activity data (includes sleep and heart rate)
            results['activity_synced'] = self.sync_activity_data(days_back)
            results['sleep_synced'] = results['activity_synced']  # Sleep data is included in activity
            
            # Sync steps data separately for more detailed tracking
            results['steps_synced'] = self.sync_steps_data(days_back)
            
            # Heart rate is already synced in activity_data, but we can sync separately if needed
            results['heart_rate_synced'] = self.sync_heart_rate_data(days_back)
            
        except Exception as e:
            logger.error(f"Failed to sync all data: {e}")
            raise
        
        return results 