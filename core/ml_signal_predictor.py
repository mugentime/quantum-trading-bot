"""
Machine Learning Signal Predictor
Implements ML models for signal strength prediction and optimal exit timing
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
import joblib
import os

logger = logging.getLogger(__name__)

class MLSignalPredictor:
    """Machine Learning system for signal prediction and optimization"""
    
    def __init__(self):
        # Model storage
        self.signal_strength_model = None
        self.exit_timing_model = None
        self.regime_classifier = None
        self.scalers = {}
        
        # Model parameters
        self.min_training_samples = 50
        self.feature_window = 24  # Hours of features to use
        self.retrain_threshold = 100  # Retrain after this many new samples
        
        # Training data storage
        self.training_data = []
        self.model_performance = {}
        
        # Feature engineering parameters
        self.technical_indicators = ['sma', 'ema', 'rsi', 'macd', 'bollinger']
        
        # Model file paths
        self.model_dir = "models"
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Load existing models if available
        self._load_existing_models()
    
    async def predict_signal_strength(self, signal_data: Dict, market_data: Dict = None) -> Dict:
        """
        Predict signal strength using ML model
        
        Args:
            signal_data: Current signal information
            market_data: Additional market context data
            
        Returns:
            ML-enhanced signal prediction
        """
        try:
            if self.signal_strength_model is None:
                logger.warning("Signal strength model not trained, using fallback")
                return self._fallback_signal_prediction(signal_data)
            
            # Extract features from signal and market data
            features = await self._extract_signal_features(signal_data, market_data)
            
            if not features:
                return self._fallback_signal_prediction(signal_data)
            
            # Scale features
            feature_array = np.array(features).reshape(1, -1)
            if 'signal_strength' in self.scalers:
                feature_array = self.scalers['signal_strength'].transform(feature_array)
            
            # Predict signal strength
            predicted_strength = self.signal_strength_model.predict(feature_array)[0]
            predicted_strength = max(0.0, min(1.0, predicted_strength))  # Bound between 0-1
            
            # Get prediction confidence
            if hasattr(self.signal_strength_model, 'predict_proba'):
                confidence_scores = self.signal_strength_model.predict_proba(feature_array)[0]
                confidence = max(confidence_scores) if len(confidence_scores) > 0 else 0.7
            else:
                # For regression models, estimate confidence from feature quality
                confidence = self._estimate_prediction_confidence(features)
            
            # Generate enhanced signal
            enhanced_signal = {
                'original_strength': signal_data.get('deviation', 0.0),
                'ml_predicted_strength': predicted_strength,
                'confidence': confidence,
                'features_used': len(features),
                'model_type': type(self.signal_strength_model).__name__,
                'enhancement_factor': predicted_strength / max(0.01, signal_data.get('deviation', 0.01)),
                'final_strength': (predicted_strength + signal_data.get('deviation', 0.0)) / 2,  # Average
                'timestamp': datetime.now()
            }
            
            logger.info(f"ML signal strength prediction: original={signal_data.get('deviation', 0):.3f}, "
                       f"predicted={predicted_strength:.3f}, confidence={confidence:.3f}")
            
            return enhanced_signal
            
        except Exception as e:
            logger.error(f"Error in ML signal prediction: {e}")
            return self._fallback_signal_prediction(signal_data)
    
    async def predict_optimal_exit_timing(self, position_data: Dict, market_conditions: Dict = None) -> Dict:
        """
        Predict optimal exit timing using ML model
        
        Args:
            position_data: Current position information
            market_conditions: Market context data
            
        Returns:
            ML-predicted optimal exit timing
        """
        try:
            if self.exit_timing_model is None:
                logger.warning("Exit timing model not trained, using fallback")
                return self._fallback_exit_timing(position_data)
            
            # Extract features for exit timing prediction
            features = await self._extract_exit_features(position_data, market_conditions)
            
            if not features:
                return self._fallback_exit_timing(position_data)
            
            # Scale features
            feature_array = np.array(features).reshape(1, -1)
            if 'exit_timing' in self.scalers:
                feature_array = self.scalers['exit_timing'].transform(feature_array)
            
            # Predict exit timing (in minutes)
            predicted_minutes = self.exit_timing_model.predict(feature_array)[0]
            predicted_minutes = max(30, min(360, predicted_minutes))  # 30min to 6 hours
            
            # Predict exit type (time-based, profit-based, or loss-based)
            exit_type = self._predict_exit_type(features, position_data)
            
            # Calculate confidence
            confidence = self._estimate_exit_confidence(features, position_data)
            
            result = {
                'predicted_exit_minutes': predicted_minutes,
                'exit_type': exit_type,
                'confidence': confidence,
                'features_used': len(features),
                'current_position_age': self._calculate_position_age(position_data),
                'recommendation': self._generate_exit_recommendation(predicted_minutes, exit_type, confidence),
                'timestamp': datetime.now()
            }
            
            logger.info(f"ML exit timing prediction: {predicted_minutes:.0f} minutes, "
                       f"type={exit_type}, confidence={confidence:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in ML exit timing prediction: {e}")
            return self._fallback_exit_timing(position_data)
    
    async def classify_market_regime(self, market_data: Dict) -> Dict:
        """
        Classify market regime using ML model
        
        Args:
            market_data: Market data for classification
            
        Returns:
            ML-classified market regime
        """
        try:
            if self.regime_classifier is None:
                logger.warning("Regime classifier not trained, using fallback")
                return {'regime': 'unknown', 'confidence': 0.5}
            
            # Extract regime features
            features = await self._extract_regime_features(market_data)
            
            if not features:
                return {'regime': 'unknown', 'confidence': 0.5}
            
            # Scale features
            feature_array = np.array(features).reshape(1, -1)
            if 'regime_classification' in self.scalers:
                feature_array = self.scalers['regime_classification'].transform(feature_array)
            
            # Classify regime
            predicted_regime_idx = self.regime_classifier.predict(feature_array)[0]
            regime_probs = self.regime_classifier.predict_proba(feature_array)[0]
            
            # Map to regime names
            regime_names = ['bull', 'bear', 'sideways', 'volatile']
            predicted_regime = regime_names[min(predicted_regime_idx, len(regime_names)-1)]
            confidence = max(regime_probs)
            
            return {
                'regime': predicted_regime,
                'confidence': confidence,
                'probabilities': dict(zip(regime_names, regime_probs)),
                'features_used': len(features),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error in ML regime classification: {e}")
            return {'regime': 'unknown', 'confidence': 0.5, 'error': str(e)}
    
    async def train_models(self, historical_data: List[Dict]) -> Dict:
        """
        Train ML models with historical data
        
        Args:
            historical_data: Historical trading and market data
            
        Returns:
            Training results and performance metrics
        """
        try:
            if len(historical_data) < self.min_training_samples:
                logger.warning(f"Insufficient data for training: {len(historical_data)} < {self.min_training_samples}")
                return {'status': 'insufficient_data', 'samples': len(historical_data)}
            
            logger.info(f"Training ML models with {len(historical_data)} samples")
            
            # Prepare training data
            signal_features, signal_targets = await self._prepare_signal_training_data(historical_data)
            exit_features, exit_targets = await self._prepare_exit_training_data(historical_data)
            regime_features, regime_targets = await self._prepare_regime_training_data(historical_data)
            
            results = {}
            
            # Train signal strength model
            if len(signal_features) >= self.min_training_samples:
                signal_result = self._train_signal_strength_model(signal_features, signal_targets)
                results['signal_strength'] = signal_result
            
            # Train exit timing model
            if len(exit_features) >= self.min_training_samples:
                exit_result = self._train_exit_timing_model(exit_features, exit_targets)
                results['exit_timing'] = exit_result
            
            # Train regime classifier
            if len(regime_features) >= self.min_training_samples:
                regime_result = self._train_regime_classifier(regime_features, regime_targets)
                results['regime_classification'] = regime_result
            
            # Save models
            self._save_models()
            
            logger.info(f"ML model training completed: {len(results)} models trained")
            
            return {
                'status': 'success',
                'models_trained': len(results),
                'training_samples': len(historical_data),
                'results': results,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error training ML models: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _extract_signal_features(self, signal_data: Dict, market_data: Dict = None) -> List[float]:
        """Extract features for signal strength prediction"""
        try:
            features = []
            
            # Basic signal features
            features.extend([
                signal_data.get('correlation', 0.0),
                signal_data.get('deviation', 0.0),
                abs(signal_data.get('correlation', 0.0)),  # Absolute correlation
                signal_data.get('deviation', 0.0) ** 2,    # Squared deviation
            ])
            
            # Market context features
            if market_data:
                features.extend([
                    market_data.get('volatility', 0.03),
                    market_data.get('volume_ratio', 1.0),
                    market_data.get('price_change_1h', 0.0),
                    market_data.get('price_change_4h', 0.0),
                    market_data.get('price_change_24h', 0.0),
                ])
            
            # Time-based features
            now = datetime.now()
            features.extend([
                now.hour / 24.0,                    # Hour of day (normalized)
                now.weekday() / 6.0,               # Day of week (normalized)
                (now.timestamp() % 86400) / 86400  # Time within day
            ])
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting signal features: {e}")
            return []
    
    async def _extract_exit_features(self, position_data: Dict, market_conditions: Dict = None) -> List[float]:
        """Extract features for exit timing prediction"""
        try:
            features = []
            
            # Position features
            entry_time = position_data.get('entry_time')
            if isinstance(entry_time, str):
                entry_time = datetime.fromisoformat(entry_time.replace('T', ' '))
            elif isinstance(entry_time, datetime):
                entry_time = entry_time
            else:
                entry_time = datetime.now() - timedelta(hours=1)  # Default
            
            position_age_hours = (datetime.now() - entry_time).total_seconds() / 3600
            
            features.extend([
                position_age_hours,
                position_data.get('entry_price', 0.0),
                position_data.get('current_profit_pct', 0.0),
                abs(position_data.get('current_profit_pct', 0.0)),
                position_data.get('leverage', 1.0),
            ])
            
            # Market condition features
            if market_conditions:
                features.extend([
                    market_conditions.get('volatility_regime_score', 0.5),
                    market_conditions.get('trend_strength', 0.0),
                    market_conditions.get('volume_trend', 1.0),
                ])
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting exit features: {e}")
            return []
    
    async def _extract_regime_features(self, market_data: Dict) -> List[float]:
        """Extract features for regime classification"""
        try:
            features = []
            
            # Volatility features
            features.extend([
                market_data.get('daily_volatility', 0.03),
                market_data.get('weekly_volatility', 0.05),
                market_data.get('volatility_trend', 0.0),
            ])
            
            # Price movement features
            features.extend([
                market_data.get('price_change_1d', 0.0),
                market_data.get('price_change_7d', 0.0),
                market_data.get('price_change_30d', 0.0),
            ])
            
            # Technical indicators
            features.extend([
                market_data.get('rsi', 50.0) / 100.0,         # Normalized RSI
                market_data.get('macd_signal', 0.0),
                market_data.get('bollinger_position', 0.5),    # Position in Bollinger bands
            ])
            
            # Volume features
            features.extend([
                market_data.get('volume_sma_ratio', 1.0),
                market_data.get('volume_trend', 0.0),
            ])
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting regime features: {e}")
            return []
    
    def _train_signal_strength_model(self, features: List[List[float]], targets: List[float]) -> Dict:
        """Train signal strength prediction model"""
        try:
            X = np.array(features)
            y = np.array(targets)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train Random Forest model
            model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_score = model.score(X_train_scaled, y_train)
            test_score = model.score(X_test_scaled, y_test)
            
            # Store model and scaler
            self.signal_strength_model = model
            self.scalers['signal_strength'] = scaler
            
            return {
                'model_type': 'RandomForestRegressor',
                'train_score': train_score,
                'test_score': test_score,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'feature_count': X.shape[1]
            }
            
        except Exception as e:
            logger.error(f"Error training signal strength model: {e}")
            return {'error': str(e)}
    
    def _train_exit_timing_model(self, features: List[List[float]], targets: List[float]) -> Dict:
        """Train exit timing prediction model"""
        try:
            X = np.array(features)
            y = np.array(targets)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train Gradient Boosting model
            model = GradientBoostingClassifier(n_estimators=100, random_state=42, max_depth=6)
            
            # Convert continuous targets to discrete classes (time bins)
            y_train_classes = np.digitize(y_train, bins=[30, 60, 120, 240, 360]) - 1  # 5 classes
            y_test_classes = np.digitize(y_test, bins=[30, 60, 120, 240, 360]) - 1
            
            model.fit(X_train_scaled, y_train_classes)
            
            # Evaluate
            train_accuracy = accuracy_score(y_train_classes, model.predict(X_train_scaled))
            test_accuracy = accuracy_score(y_test_classes, model.predict(X_test_scaled))
            
            # Store model and scaler
            self.exit_timing_model = model
            self.scalers['exit_timing'] = scaler
            
            return {
                'model_type': 'GradientBoostingClassifier',
                'train_accuracy': train_accuracy,
                'test_accuracy': test_accuracy,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'feature_count': X.shape[1]
            }
            
        except Exception as e:
            logger.error(f"Error training exit timing model: {e}")
            return {'error': str(e)}
    
    def _train_regime_classifier(self, features: List[List[float]], targets: List[int]) -> Dict:
        """Train regime classification model"""
        try:
            X = np.array(features)
            y = np.array(targets)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train Random Forest classifier
            model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=8)
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_accuracy = accuracy_score(y_train, model.predict(X_train_scaled).round().astype(int))
            test_accuracy = accuracy_score(y_test, model.predict(X_test_scaled).round().astype(int))
            
            # Store model and scaler
            self.regime_classifier = model
            self.scalers['regime_classification'] = scaler
            
            return {
                'model_type': 'RandomForestClassifier',
                'train_accuracy': train_accuracy,
                'test_accuracy': test_accuracy,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'feature_count': X.shape[1]
            }
            
        except Exception as e:
            logger.error(f"Error training regime classifier: {e}")
            return {'error': str(e)}
    
    async def _prepare_signal_training_data(self, historical_data: List[Dict]) -> Tuple[List[List[float]], List[float]]:
        """Prepare training data for signal strength model"""
        features = []
        targets = []
        
        for record in historical_data:
            if 'signal_data' in record and 'actual_performance' in record:
                signal_features = await self._extract_signal_features(
                    record['signal_data'], 
                    record.get('market_data')
                )
                if signal_features:
                    features.append(signal_features)
                    # Target is actual performance (normalized)
                    performance = record['actual_performance'].get('profit_pct', 0.0)
                    targets.append(min(1.0, max(0.0, (performance + 0.05) / 0.1)))  # Normalize to 0-1
        
        return features, targets
    
    async def _prepare_exit_training_data(self, historical_data: List[Dict]) -> Tuple[List[List[float]], List[float]]:
        """Prepare training data for exit timing model"""
        features = []
        targets = []
        
        for record in historical_data:
            if 'position_data' in record and 'exit_data' in record:
                exit_features = await self._extract_exit_features(
                    record['position_data'],
                    record.get('market_conditions')
                )
                if exit_features:
                    features.append(exit_features)
                    # Target is actual exit time in minutes
                    exit_minutes = record['exit_data'].get('duration_minutes', 120)
                    targets.append(min(360, max(30, exit_minutes)))  # Bound to 30min-6hr
        
        return features, targets
    
    async def _prepare_regime_training_data(self, historical_data: List[Dict]) -> Tuple[List[List[float]], List[int]]:
        """Prepare training data for regime classifier"""
        features = []
        targets = []
        
        regime_mapping = {'bull': 0, 'bear': 1, 'sideways': 2, 'volatile': 3}
        
        for record in historical_data:
            if 'market_data' in record and 'regime_label' in record:
                regime_features = await self._extract_regime_features(record['market_data'])
                if regime_features:
                    features.append(regime_features)
                    regime_label = record['regime_label']
                    targets.append(regime_mapping.get(regime_label, 2))  # Default to sideways
        
        return features, targets
    
    def _fallback_signal_prediction(self, signal_data: Dict) -> Dict:
        """Fallback signal prediction when ML model unavailable"""
        return {
            'original_strength': signal_data.get('deviation', 0.0),
            'ml_predicted_strength': signal_data.get('deviation', 0.0),
            'confidence': 0.5,
            'features_used': 0,
            'model_type': 'fallback',
            'enhancement_factor': 1.0,
            'final_strength': signal_data.get('deviation', 0.0),
            'timestamp': datetime.now()
        }
    
    def _fallback_exit_timing(self, position_data: Dict) -> Dict:
        """Fallback exit timing when ML model unavailable"""
        return {
            'predicted_exit_minutes': 120,  # 2 hours default
            'exit_type': 'time_based',
            'confidence': 0.5,
            'features_used': 0,
            'current_position_age': 0,
            'recommendation': 'hold',
            'timestamp': datetime.now()
        }
    
    def _estimate_prediction_confidence(self, features: List[float]) -> float:
        """Estimate prediction confidence based on feature quality"""
        if not features:
            return 0.3
        
        # Simple heuristic: more features and less extreme values = higher confidence
        feature_count_factor = min(1.0, len(features) / 10.0)
        feature_quality_factor = 1.0 - (np.std(features) / (np.mean(np.abs(features)) + 0.01))
        
        return max(0.3, min(0.9, (feature_count_factor + feature_quality_factor) / 2))
    
    def _calculate_position_age(self, position_data: Dict) -> float:
        """Calculate position age in hours"""
        try:
            entry_time = position_data.get('entry_time')
            if isinstance(entry_time, str):
                entry_time = datetime.fromisoformat(entry_time.replace('T', ' '))
            elif isinstance(entry_time, datetime):
                entry_time = entry_time
            else:
                return 1.0  # Default 1 hour
            
            return (datetime.now() - entry_time).total_seconds() / 3600
            
        except Exception as e:
            logger.error(f"Error calculating position age: {e}")
            return 1.0
    
    def _predict_exit_type(self, features: List[float], position_data: Dict) -> str:
        """Predict exit type based on features"""
        current_profit = position_data.get('current_profit_pct', 0.0)
        
        if current_profit > 0.02:  # 2% profit
            return 'profit_based'
        elif current_profit < -0.015:  # 1.5% loss
            return 'loss_based'
        else:
            return 'time_based'
    
    def _estimate_exit_confidence(self, features: List[float], position_data: Dict) -> float:
        """Estimate exit timing confidence"""
        base_confidence = self._estimate_prediction_confidence(features)
        
        # Adjust based on position characteristics
        profit_pct = position_data.get('current_profit_pct', 0.0)
        if abs(profit_pct) > 0.03:  # Strong profit/loss signal
            base_confidence *= 1.2
        
        return max(0.3, min(0.9, base_confidence))
    
    def _generate_exit_recommendation(self, predicted_minutes: float, exit_type: str, confidence: float) -> str:
        """Generate exit recommendation"""
        if confidence < 0.4:
            return 'hold'  # Low confidence
        
        if exit_type == 'profit_based' and confidence > 0.7:
            return 'take_profit'
        elif exit_type == 'loss_based' and confidence > 0.6:
            return 'stop_loss'
        elif predicted_minutes < 60 and confidence > 0.6:
            return 'exit_soon'
        else:
            return 'hold'
    
    def _save_models(self):
        """Save trained models to disk"""
        try:
            if self.signal_strength_model:
                joblib.dump(self.signal_strength_model, 
                           os.path.join(self.model_dir, 'signal_strength_model.pkl'))
            
            if self.exit_timing_model:
                joblib.dump(self.exit_timing_model,
                           os.path.join(self.model_dir, 'exit_timing_model.pkl'))
            
            if self.regime_classifier:
                joblib.dump(self.regime_classifier,
                           os.path.join(self.model_dir, 'regime_classifier.pkl'))
            
            if self.scalers:
                joblib.dump(self.scalers,
                           os.path.join(self.model_dir, 'scalers.pkl'))
            
            logger.info("ML models saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def _load_existing_models(self):
        """Load existing models from disk"""
        try:
            signal_path = os.path.join(self.model_dir, 'signal_strength_model.pkl')
            if os.path.exists(signal_path):
                self.signal_strength_model = joblib.load(signal_path)
            
            exit_path = os.path.join(self.model_dir, 'exit_timing_model.pkl')
            if os.path.exists(exit_path):
                self.exit_timing_model = joblib.load(exit_path)
            
            regime_path = os.path.join(self.model_dir, 'regime_classifier.pkl')
            if os.path.exists(regime_path):
                self.regime_classifier = joblib.load(regime_path)
            
            scalers_path = os.path.join(self.model_dir, 'scalers.pkl')
            if os.path.exists(scalers_path):
                self.scalers = joblib.load(scalers_path)
            
            models_loaded = sum([
                self.signal_strength_model is not None,
                self.exit_timing_model is not None,
                self.regime_classifier is not None
            ])
            
            if models_loaded > 0:
                logger.info(f"Loaded {models_loaded} existing ML models")
            
        except Exception as e:
            logger.error(f"Error loading existing models: {e}")
    
    def add_training_sample(self, sample_data: Dict):
        """Add new training sample for model retraining"""
        try:
            self.training_data.append({
                'timestamp': datetime.now(),
                **sample_data
            })
            
            # Check if retraining is needed
            if len(self.training_data) >= self.retrain_threshold:
                logger.info(f"Triggering model retraining with {len(self.training_data)} samples")
                # In a production system, this would trigger async retraining
                
        except Exception as e:
            logger.error(f"Error adding training sample: {e}")
    
    def get_model_status(self) -> Dict:
        """Get current model status and performance"""
        return {
            'signal_strength_model': self.signal_strength_model is not None,
            'exit_timing_model': self.exit_timing_model is not None,
            'regime_classifier': self.regime_classifier is not None,
            'scalers_loaded': len(self.scalers),
            'training_samples': len(self.training_data),
            'model_performance': self.model_performance,
            'retrain_threshold': self.retrain_threshold
        }

# Global instance
ml_signal_predictor = MLSignalPredictor()