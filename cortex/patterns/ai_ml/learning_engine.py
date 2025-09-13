#!/usr/bin/env python3
"""
Learning Engine для FeatureFactory.
Обучается на основе результатов выполнения фич и улучшает качество работы системы.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import structlog

log = structlog.get_logger()

class LearningType(Enum):
    """Типы обучения"""
    ERROR_PATTERN = "error_pattern"
    SUCCESS_PATTERN = "success_pattern"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    CODE_QUALITY = "code_quality"
    ARCHITECTURE_IMPROVEMENT = "architecture_improvement"
    TESTING_STRATEGY = "testing_strategy"

@dataclass
class LearningExample:
    """Пример для обучения"""
    id: str
    type: LearningType
    input_features: Dict[str, Any]
    output_result: Dict[str, Any]
    success: bool
    performance_metrics: Dict[str, float]
    timestamp: datetime
    correlation_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Pattern:
    """Выявленный паттерн"""
    id: str
    type: LearningType
    description: str
    conditions: List[Dict[str, Any]]
    recommendations: List[str]
    confidence: float
    examples_count: int
    last_updated: datetime
    success_rate: float

@dataclass
class Insight:
    """Инсайт полученный из анализа данных"""
    id: str
    title: str
    description: str
    impact_score: float
    action_items: List[str]
    supporting_data: Dict[str, Any]
    created_at: datetime

class FeatureExtractor:
    """Извлечение признаков из данных о фичах"""
    
    def __init__(self):
        self.text_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.is_fitted = False
    
    def extract_features(self, example: LearningExample) -> Dict[str, Any]:
        """Извлечение признаков из примера"""
        features = {}
        
        # Текстовые признаки
        text_content = self._extract_text_content(example)
        features.update(text_content)
        
        # Численные признаки
        numeric_features = self._extract_numeric_features(example)
        features.update(numeric_features)
        
        # Категориальные признаки
        categorical_features = self._extract_categorical_features(example)
        features.update(categorical_features)
        
        return features
    
    def _extract_text_content(self, example: LearningExample) -> Dict[str, str]:
        """Извлечение текстового содержимого"""
        text_features = {}
        
        # Объединяем весь текстовый контент
        text_parts = []
        
        if 'requirements' in example.input_features:
            text_parts.append(example.input_features['requirements'])
            
        if 'code' in example.output_result:
            text_parts.append(example.output_result['code'])
            
        if 'error_message' in example.output_result:
            text_parts.append(example.output_result['error_message'])
            
        text_features['combined_text'] = ' '.join(text_parts)
        text_features['requirements_text'] = example.input_features.get('requirements', '')
        
        return text_features
    
    def _extract_numeric_features(self, example: LearningExample) -> Dict[str, float]:
        """Извлечение численных признаков"""
        features = {}
        
        # Метрики производительности
        for metric, value in example.performance_metrics.items():
            features[f'perf_{metric}'] = float(value)
        
        # Размеры и сложность
        if 'code' in example.output_result:
            code = example.output_result['code']
            features['code_length'] = len(code)
            features['code_lines'] = len(code.split('\n'))
            features['complexity_estimate'] = self._estimate_complexity(code)
        
        # Временные характеристики
        features['hour_of_day'] = example.timestamp.hour
        features['day_of_week'] = example.timestamp.weekday()
        
        return features
    
    def _extract_categorical_features(self, example: LearningExample) -> Dict[str, str]:
        """Извлечение категориальных признаков"""
        features = {}
        
        features['learning_type'] = example.type.value
        features['success'] = str(example.success)
        
        # Контекст выполнения
        if 'language' in example.input_features:
            features['programming_language'] = example.input_features['language']
            
        if 'framework' in example.input_features:
            features['framework'] = example.input_features['framework']
            
        if 'complexity_level' in example.metadata:
            features['complexity_level'] = example.metadata['complexity_level']
        
        return features
    
    def _estimate_complexity(self, code: str) -> float:
        """Простая оценка сложности кода"""
        complexity = 0
        
        # Считаем контрольные структуры
        control_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'with']
        for keyword in control_keywords:
            complexity += code.count(keyword)
        
        # Считаем функции и классы
        complexity += code.count('def ') * 2
        complexity += code.count('class ') * 3
        
        return complexity / max(len(code.split('\n')), 1)  # Нормализуем по количеству строк
    
    def fit_text_vectorizer(self, examples: List[LearningExample]):
        """Обучение текстового векторизатора"""
        texts = []
        for example in examples:
            features = self.extract_features(example)
            texts.append(features.get('combined_text', ''))
        
        if texts:
            self.text_vectorizer.fit(texts)
            self.is_fitted = True
    
    def vectorize_text(self, text: str) -> np.ndarray:
        """Векторизация текста"""
        if not self.is_fitted:
            return np.array([])
        
        return self.text_vectorizer.transform([text]).toarray()[0]

class PatternDetector:
    """Детектор паттернов в данных"""
    
    def __init__(self, feature_extractor: FeatureExtractor):
        self.feature_extractor = feature_extractor
        self.patterns: Dict[str, Pattern] = {}
        
    def detect_patterns(self, examples: List[LearningExample]) -> List[Pattern]:
        """Обнаружение паттернов в примерах"""
        patterns = []
        
        # Группируем примеры по типу обучения
        grouped_examples = self._group_by_type(examples)
        
        for learning_type, type_examples in grouped_examples.items():
            if len(type_examples) < 3:  # Минимум примеров для паттерна
                continue
                
            # Обнаруживаем паттерны ошибок
            if learning_type == LearningType.ERROR_PATTERN:
                error_patterns = self._detect_error_patterns(type_examples)
                patterns.extend(error_patterns)
            
            # Обнаруживаем паттерны успеха
            elif learning_type == LearningType.SUCCESS_PATTERN:
                success_patterns = self._detect_success_patterns(type_examples)
                patterns.extend(success_patterns)
            
            # Обнаруживаем паттерны производительности
            elif learning_type == LearningType.PERFORMANCE_OPTIMIZATION:
                perf_patterns = self._detect_performance_patterns(type_examples)
                patterns.extend(perf_patterns)
        
        # Сохраняем обнаруженные паттерны
        for pattern in patterns:
            self.patterns[pattern.id] = pattern
            
        return patterns
    
    def _group_by_type(self, examples: List[LearningExample]) -> Dict[LearningType, List[LearningExample]]:
        """Группировка примеров по типу"""
        groups = {}
        for example in examples:
            if example.type not in groups:
                groups[example.type] = []
            groups[example.type].append(example)
        return groups
    
    def _detect_error_patterns(self, examples: List[LearningExample]) -> List[Pattern]:
        """Обнаружение паттернов ошибок"""
        patterns = []
        
        # Группируем по типам ошибок
        error_groups = {}
        for example in examples:
            if not example.success and 'error_type' in example.output_result:
                error_type = example.output_result['error_type']
                if error_type not in error_groups:
                    error_groups[error_type] = []
                error_groups[error_type].append(example)
        
        # Создаем паттерны для каждого типа ошибок
        for error_type, error_examples in error_groups.items():
            if len(error_examples) >= 3:
                pattern = self._create_error_pattern(error_type, error_examples)
                patterns.append(pattern)
        
        return patterns
    
    def _detect_success_patterns(self, examples: List[LearningExample]) -> List[Pattern]:
        """Обнаружение паттернов успеха"""
        patterns = []
        
        successful_examples = [ex for ex in examples if ex.success]
        if len(successful_examples) < 5:
            return patterns
        
        # Кластеризация успешных примеров
        features_matrix = self._extract_features_matrix(successful_examples)
        if features_matrix.shape[0] > 0:
            n_clusters = min(5, len(successful_examples) // 2)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(features_matrix)
            
            # Создаем паттерны для каждого кластера
            for cluster_id in range(n_clusters):
                cluster_examples = [ex for i, ex in enumerate(successful_examples) if clusters[i] == cluster_id]
                if len(cluster_examples) >= 2:
                    pattern = self._create_success_pattern(cluster_id, cluster_examples)
                    patterns.append(pattern)
        
        return patterns
    
    def _detect_performance_patterns(self, examples: List[LearningExample]) -> List[Pattern]:
        """Обнаружение паттернов производительности"""
        patterns = []
        
        # Анализируем корреляцию между входными параметрами и производительностью
        high_perf_examples = []
        low_perf_examples = []
        
        for example in examples:
            execution_time = example.performance_metrics.get('execution_time', 0)
            if execution_time > 0:
                if execution_time < 5.0:  # Быстрое выполнение
                    high_perf_examples.append(example)
                elif execution_time > 30.0:  # Медленное выполнение
                    low_perf_examples.append(example)
        
        if len(high_perf_examples) >= 3:
            pattern = self._create_performance_pattern("high_performance", high_perf_examples, True)
            patterns.append(pattern)
        
        if len(low_perf_examples) >= 3:
            pattern = self._create_performance_pattern("low_performance", low_perf_examples, False)
            patterns.append(pattern)
        
        return patterns
    
    def _create_error_pattern(self, error_type: str, examples: List[LearningExample]) -> Pattern:
        """Создание паттерна ошибок"""
        conditions = []
        recommendations = []
        
        # Анализируем общие условия, приводящие к ошибке
        common_features = self._find_common_features(examples)
        for feature, value in common_features.items():
            conditions.append({"feature": feature, "value": value, "operator": "equals"})
        
        # Генерируем рекомендации на основе анализа
        recommendations.append(f"Избегайте {error_type} ошибок при работе с {common_features}")
        recommendations.append("Добавьте валидацию входных данных")
        recommendations.append("Улучшите обработку ошибок")
        
        return Pattern(
            id=f"error_{error_type}_{datetime.now().timestamp()}",
            type=LearningType.ERROR_PATTERN,
            description=f"Паттерн для {error_type} ошибок",
            conditions=conditions,
            recommendations=recommendations,
            confidence=min(0.9, len(examples) / 10.0),
            examples_count=len(examples),
            last_updated=datetime.now(),
            success_rate=0.0
        )
    
    def _create_success_pattern(self, cluster_id: int, examples: List[LearningExample]) -> Pattern:
        """Создание паттерна успеха"""
        conditions = []
        recommendations = []
        
        # Анализируем общие черты успешных примеров
        common_features = self._find_common_features(examples)
        for feature, value in common_features.items():
            conditions.append({"feature": feature, "value": value, "operator": "equals"})
        
        # Генерируем рекомендации
        avg_perf = np.mean([ex.performance_metrics.get('execution_time', 0) for ex in examples])
        recommendations.append(f"Используйте подход из кластера {cluster_id}")
        recommendations.append(f"Ожидаемое время выполнения: {avg_perf:.2f}с")
        
        return Pattern(
            id=f"success_{cluster_id}_{datetime.now().timestamp()}",
            type=LearningType.SUCCESS_PATTERN,
            description=f"Успешный паттерн кластера {cluster_id}",
            conditions=conditions,
            recommendations=recommendations,
            confidence=len(examples) / 10.0,
            examples_count=len(examples),
            last_updated=datetime.now(),
            success_rate=1.0
        )
    
    def _create_performance_pattern(self, perf_type: str, examples: List[LearningExample], is_good: bool) -> Pattern:
        """Создание паттерна производительности"""
        conditions = []
        recommendations = []
        
        common_features = self._find_common_features(examples)
        for feature, value in common_features.items():
            conditions.append({"feature": feature, "value": value, "operator": "equals"})
        
        if is_good:
            recommendations.append("Применяйте эти паттерны для оптимизации производительности")
            recommendations.append("Код выполняется быстро при данных условиях")
        else:
            recommendations.append("Избегайте этих паттернов для улучшения производительности") 
            recommendations.append("Рассмотрите рефакторинг или оптимизацию")
        
        return Pattern(
            id=f"perf_{perf_type}_{datetime.now().timestamp()}",
            type=LearningType.PERFORMANCE_OPTIMIZATION,
            description=f"Паттерн {perf_type} производительности",
            conditions=conditions,
            recommendations=recommendations,
            confidence=len(examples) / 10.0,
            examples_count=len(examples),
            last_updated=datetime.now(),
            success_rate=1.0 if is_good else 0.0
        )
    
    def _find_common_features(self, examples: List[LearningExample]) -> Dict[str, Any]:
        """Поиск общих признаков в примерах"""
        common_features = {}
        
        if not examples:
            return common_features
        
        # Анализируем каждый признак
        all_features = {}
        for example in examples:
            features = self.feature_extractor.extract_features(example)
            for feature_name, feature_value in features.items():
                if feature_name not in all_features:
                    all_features[feature_name] = []
                all_features[feature_name].append(feature_value)
        
        # Находим признаки, которые одинаковы в большинстве примеров
        threshold = len(examples) * 0.7  # 70% примеров должны иметь одинаковое значение
        
        for feature_name, values in all_features.items():
            if isinstance(values[0], str):
                # Для строковых признаков
                value_counts = {}
                for value in values:
                    value_counts[value] = value_counts.get(value, 0) + 1
                
                most_common_value = max(value_counts, key=value_counts.get)
                if value_counts[most_common_value] >= threshold:
                    common_features[feature_name] = most_common_value
            
            elif isinstance(values[0], (int, float)):
                # Для численных признаков
                mean_value = np.mean(values)
                std_value = np.std(values)
                if std_value < mean_value * 0.2:  # Малый разброс
                    common_features[feature_name] = mean_value
        
        return common_features
    
    def _extract_features_matrix(self, examples: List[LearningExample]) -> np.ndarray:
        """Извлечение матрицы признаков для кластеризации"""
        features_list = []
        
        for example in examples:
            features = self.feature_extractor.extract_features(example)
            
            # Преобразуем в численный вектор
            numeric_features = []
            for key, value in features.items():
                if isinstance(value, (int, float)):
                    numeric_features.append(value)
                elif isinstance(value, bool):
                    numeric_features.append(1.0 if value else 0.0)
                elif isinstance(value, str):
                    # Хешируем строки в числа
                    numeric_features.append(hash(value) % 1000)
            
            features_list.append(numeric_features)
        
        if features_list:
            # Приводим к одинаковой длине
            max_len = max(len(f) for f in features_list)
            padded_features = []
            for features in features_list:
                padded = features + [0.0] * (max_len - len(features))
                padded_features.append(padded)
            
            return np.array(padded_features)
        
        return np.array([])

class LearningEngine:
    """Основной движок обучения"""
    
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.pattern_detector = PatternDetector(self.feature_extractor)
        self.examples: List[LearningExample] = []
        self.insights: List[Insight] = []
        
    async def learn_from_example(self, example: LearningExample):
        """Обучение на одном примере"""
        self.examples.append(example)
        
        log.info(
            event="learning_example_added",
            example_id=example.id,
            type=example.type.value,
            success=example.success,
            correlation_id=example.correlation_id
        )
        
        # Переобучаем модель если накопилось достаточно примеров
        if len(self.examples) % 50 == 0:  # Каждые 50 примеров
            await self._retrain()
    
    async def batch_learn(self, examples: List[LearningExample]):
        """Пакетное обучение"""
        self.examples.extend(examples)
        
        # Обучаем векторизатор
        self.feature_extractor.fit_text_vectorizer(self.examples)
        
        # Обнаруживаем паттерны
        patterns = self.pattern_detector.detect_patterns(self.examples)
        
        # Генерируем инсайты
        insights = await self._generate_insights(patterns)
        self.insights.extend(insights)
        
        log.info(
            event="batch_learning_completed",
            examples_count=len(examples),
            patterns_found=len(patterns),
            insights_generated=len(insights)
        )
    
    async def _retrain(self):
        """Переобучение модели"""
        # Обновляем векторизатор
        self.feature_extractor.fit_text_vectorizer(self.examples)
        
        # Переобнаруживаем паттерны
        recent_examples = self.examples[-200:]  # Последние 200 примеров
        patterns = self.pattern_detector.detect_patterns(recent_examples)
        
        # Генерируем новые инсайты
        new_insights = await self._generate_insights(patterns)
        self.insights.extend(new_insights)
        
        log.info(
            event="model_retrained",
            total_examples=len(self.examples),
            patterns_updated=len(patterns),
            new_insights=len(new_insights)
        )
    
    async def _generate_insights(self, patterns: List[Pattern]) -> List[Insight]:
        """Генерация инсайтов из паттернов"""
        insights = []
        
        for pattern in patterns:
            if pattern.confidence > 0.7 and pattern.examples_count >= 5:
                insight = await self._create_insight_from_pattern(pattern)
                if insight:
                    insights.append(insight)
        
        return insights
    
    async def _create_insight_from_pattern(self, pattern: Pattern) -> Optional[Insight]:
        """Создание инсайта из паттерна"""
        if pattern.type == LearningType.ERROR_PATTERN:
            return Insight(
                id=f"insight_error_{pattern.id}",
                title=f"Обнаружен паттерн ошибок: {pattern.description}",
                description=f"Найден паттерн ошибок с {pattern.examples_count} примерами и confidence {pattern.confidence:.2f}",
                impact_score=pattern.confidence * pattern.examples_count / 10,
                action_items=pattern.recommendations,
                supporting_data={
                    "pattern_id": pattern.id,
                    "examples_count": pattern.examples_count,
                    "confidence": pattern.confidence
                },
                created_at=datetime.now()
            )
        
        elif pattern.type == LearningType.SUCCESS_PATTERN:
            return Insight(
                id=f"insight_success_{pattern.id}",
                title=f"Найден успешный паттерн: {pattern.description}",
                description=f"Обнаружен паттерн успешного выполнения с {pattern.examples_count} примерами",
                impact_score=pattern.confidence * pattern.examples_count / 5,
                action_items=pattern.recommendations,
                supporting_data={
                    "pattern_id": pattern.id,
                    "success_rate": pattern.success_rate,
                    "examples_count": pattern.examples_count
                },
                created_at=datetime.now()
            )
        
        return None
    
    def get_recommendations(self, context: Dict[str, Any]) -> List[str]:
        """Получение рекомендаций на основе контекста"""
        recommendations = []
        
        # Извлекаем признаки из контекста
        dummy_example = LearningExample(
            id="temp",
            type=LearningType.SUCCESS_PATTERN,
            input_features=context,
            output_result={},
            success=True,
            performance_metrics={},
            timestamp=datetime.now(),
            correlation_id="temp"
        )
        
        context_features = self.feature_extractor.extract_features(dummy_example)
        
        # Ищем подходящие паттерны
        for pattern in self.pattern_detector.patterns.values():
            if self._matches_pattern(context_features, pattern):
                recommendations.extend(pattern.recommendations)
        
        return list(set(recommendations))  # Убираем дубликаты
    
    def _matches_pattern(self, features: Dict[str, Any], pattern: Pattern) -> bool:
        """Проверка соответствия признаков паттерну"""
        matches = 0
        total_conditions = len(pattern.conditions)
        
        if total_conditions == 0:
            return False
        
        for condition in pattern.conditions:
            feature_name = condition["feature"]
            expected_value = condition["value"]
            operator = condition.get("operator", "equals")
            
            if feature_name in features:
                actual_value = features[feature_name]
                
                if operator == "equals" and actual_value == expected_value:
                    matches += 1
                elif operator == "greater" and actual_value > expected_value:
                    matches += 1
                elif operator == "less" and actual_value < expected_value:
                    matches += 1
        
        # Паттерн совпадает если больше 70% условий выполнено
        return matches / total_conditions >= 0.7
    
    def get_insights(self, limit: int = 10) -> List[Insight]:
        """Получение топ инсайтов"""
        sorted_insights = sorted(
            self.insights, 
            key=lambda x: (x.impact_score, x.created_at),
            reverse=True
        )
        return sorted_insights[:limit]
    
    def save_model(self, filepath: str):
        """Сохранение модели на диск"""
        model_data = {
            'examples': self.examples,
            'patterns': self.pattern_detector.patterns,
            'insights': self.insights,
            'vectorizer': self.feature_extractor.text_vectorizer if self.feature_extractor.is_fitted else None
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        log.info(event="model_saved", filepath=filepath)
    
    def load_model(self, filepath: str):
        """Загрузка модели с диска"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.examples = model_data['examples']
        self.pattern_detector.patterns = model_data['patterns']
        self.insights = model_data['insights']
        
        if model_data['vectorizer']:
            self.feature_extractor.text_vectorizer = model_data['vectorizer']
            self.feature_extractor.is_fitted = True
        
        log.info(event="model_loaded", filepath=filepath)

# Пример использования
async def main():
    """Демонстрация работы Learning Engine"""
    
    engine = LearningEngine()
    
    # Создаем примеры для обучения
    examples = [
        LearningExample(
            id="example_1",
            type=LearningType.ERROR_PATTERN,
            input_features={"requirements": "Create API endpoint", "language": "python"},
            output_result={"error_type": "validation_error", "error_message": "Invalid input"},
            success=False,
            performance_metrics={"execution_time": 15.0},
            timestamp=datetime.now(),
            correlation_id="test_001"
        ),
        LearningExample(
            id="example_2", 
            type=LearningType.SUCCESS_PATTERN,
            input_features={"requirements": "Create API endpoint", "language": "python"},
            output_result={"code": "def api_endpoint(): return {'status': 'ok'}"},
            success=True,
            performance_metrics={"execution_time": 3.5, "code_quality": 0.85},
            timestamp=datetime.now(),
            correlation_id="test_002"
        )
    ]
    
    # Обучаем на примерах
    await engine.batch_learn(examples)
    
    # Получаем рекомендации
    context = {"language": "python", "requirements": "Create API endpoint"}
    recommendations = engine.get_recommendations(context)
    
    print("Рекомендации:")
    for rec in recommendations:
        print(f"- {rec}")
    
    # Получаем инсайты
    insights = engine.get_insights()
    print(f"\nИнсайты ({len(insights)}):")
    for insight in insights:
        print(f"- {insight.title}: {insight.description}")

if __name__ == "__main__":
    asyncio.run(main())