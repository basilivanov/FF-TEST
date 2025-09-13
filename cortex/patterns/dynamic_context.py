# Dynamic Context Engine for FeatureFactory
# Integrates with symbol_index and call_graph for context-aware content generation

import os
import re
import json
from typing import List, Dict, Any, Optional, Set, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import structlog

class DynamicContextEngine:
    """Engine for generating dynamic context based on task analysis and code indexing"""
    
    def __init__(self, index_db_path: str = "/opt/feature-factory/data/index.db"):
        self.index_db_path = index_db_path
        self.logger = structlog.get_logger()
        self._setup_index_connection()
    
    def _setup_index_connection(self):
        """Setup connection to symbol index database"""
        try:
            self.engine = create_engine(f"sqlite:///{self.index_db_path}")
            self.logger.info("index_connection_established", db_path=self.index_db_path)
        except Exception as e:
            self.logger.warning("index_connection_failed", error=str(e))
            self.engine = None
    
    def extract_task_keywords(self, task_description: str, context_hints: List[str]) -> Set[str]:
        """Extract technical keywords from task description and context"""
        
        # Technical patterns to look for
        patterns = {
            'api_patterns': r'\b(endpoint|route|API|REST|GET|POST|PUT|DELETE|FastAPI)\b',
            'db_patterns': r'\b(database|DB|table|migration|SQLAlchemy|Alembic|schema|model)\b',
            'function_patterns': r'\b(function|method|class|def|async|await)\b',
            'file_patterns': r'\b(\w+\.py|\w+\.md|\w+\.yaml|\w+\.json)\b',
            'module_patterns': r'\b(import|from|module|package)\b',
            'test_patterns': r'\b(test|pytest|coverage|mock|fixture)\b'
        }
        
        keywords = set()
        full_text = f"{task_description} {' '.join(context_hints)}"
        
        for pattern_type, pattern in patterns.items():
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            keywords.update(match.lower() for match in matches)
        
        # Extract file paths
        file_paths = re.findall(r'/[\w/.-]+\.(?:py|md|yaml|json)', full_text)
        keywords.update(os.path.basename(path) for path in file_paths)
        
        # Extract class/function names (CamelCase and snake_case)
        identifiers = re.findall(r'\b[A-Z][a-zA-Z0-9]*\b|\b[a-z_][a-z0-9_]*\b', full_text)
        keywords.update(id for id in identifiers if len(id) > 2)
        
        self.logger.debug("keywords_extracted", count=len(keywords), 
                         keywords=list(keywords)[:10])  # Log first 10 keywords
        
        return keywords
    
    def find_relevant_symbols(self, keywords: Set[str], limit: int = 20) -> List[Dict[str, Any]]:
        """Find relevant symbols from the code index based on keywords"""
        
        if not self.engine:
            self.logger.warning("index_unavailable", message="Using fallback without symbol lookup")
            return []
        
        try:
            with self.engine.connect() as conn:
                # Build dynamic query based on keywords
                keyword_conditions = []
                params = {}
                
                for i, keyword in enumerate(list(keywords)[:10]):  # Limit to 10 keywords for query
                    keyword_conditions.append(f"symbol_name LIKE :keyword_{i}")
                    params[f"keyword_{i}"] = f"%{keyword}%"
                
                if not keyword_conditions:
                    return []
                
                query = f"""
                    SELECT file_path, symbol_name, symbol_type, line_start, line_end
                    FROM symbol_index 
                    WHERE ({' OR '.join(keyword_conditions)})
                    ORDER BY 
                        CASE 
                            WHEN symbol_type = 'class' THEN 1
                            WHEN symbol_type = 'function' THEN 2
                            WHEN symbol_type = 'method' THEN 3
                            ELSE 4
                        END,
                        symbol_name
                    LIMIT :limit
                """
                
                params['limit'] = limit
                result = conn.execute(text(query), params)
                
                symbols = []
                for row in result:
                    symbols.append({
                        'file_path': row[0],
                        'symbol_name': row[1],
                        'symbol_type': row[2],
                        'line_start': row[3],
                        'line_end': row[4],
                        'relevance_score': self._calculate_relevance(row[1], keywords)
                    })
                
                # Sort by relevance score descending
                symbols.sort(key=lambda x: x['relevance_score'], reverse=True)
                
                self.logger.info("symbols_found", count=len(symbols))
                return symbols
                
        except SQLAlchemyError as e:
            self.logger.error("symbol_query_failed", error=str(e))
            return []
    
    def find_call_relationships(self, symbols: List[Dict[str, Any]], limit: int = 15) -> List[Dict[str, Any]]:
        """Find call graph relationships for the given symbols"""
        
        if not self.engine or not symbols:
            return []
        
        try:
            with self.engine.connect() as conn:
                symbol_names = [s['symbol_name'] for s in symbols]
                
                # Build query for call graph edges
                name_conditions = []
                params = {}
                
                for i, symbol_name in enumerate(symbol_names[:10]):
                    name_conditions.append(f"source_symbol LIKE :source_{i} OR target_symbol LIKE :target_{i}")
                    params[f"source_{i}"] = f"%{symbol_name}%"
                    params[f"target_{i}"] = f"%{symbol_name}%"
                
                if not name_conditions:
                    return []
                
                query = f"""
                    SELECT source_symbol, target_symbol, file_path, line_number
                    FROM call_graph_edges
                    WHERE ({' OR '.join(name_conditions)})
                    ORDER BY source_symbol, target_symbol
                    LIMIT :limit
                """
                
                params['limit'] = limit
                result = conn.execute(text(query), params)
                
                relationships = []
                for row in result:
                    relationships.append({
                        'source_symbol': row[0],
                        'target_symbol': row[1],
                        'file_path': row[2],
                        'line_number': row[3]
                    })
                
                self.logger.info("call_relationships_found", count=len(relationships))
                return relationships
                
        except SQLAlchemyError as e:
            self.logger.error("call_graph_query_failed", error=str(e))
            return []
    
    def _calculate_relevance(self, symbol_name: str, keywords: Set[str]) -> float:
        """Calculate relevance score for a symbol based on keywords"""
        
        symbol_lower = symbol_name.lower()
        score = 0.0
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Exact match gets highest score
            if symbol_lower == keyword_lower:
                score += 1.0
            # Contains keyword gets partial score
            elif keyword_lower in symbol_lower:
                score += 0.6
            # Similar words (edit distance) get lower score
            elif self._similar_strings(symbol_lower, keyword_lower):
                score += 0.3
        
        return score
    
    def _similar_strings(self, s1: str, s2: str, threshold: float = 0.7) -> bool:
        """Check if two strings are similar using simple heuristics"""
        
        if len(s1) < 3 or len(s2) < 3:
            return False
        
        # Check if one string contains most characters from another
        common_chars = set(s1) & set(s2)
        similarity = len(common_chars) / max(len(set(s1)), len(set(s2)))
        
        return similarity >= threshold
    
    def generate_code_examples(self, symbols: List[Dict[str, Any]], 
                              relationships: List[Dict[str, Any]]) -> Dict[str, str]:
        """Generate code examples based on found symbols and relationships"""
        
        examples = {}
        
        # Group symbols by type
        by_type = {}
        for symbol in symbols[:10]:  # Limit to top 10 relevant symbols
            symbol_type = symbol['symbol_type']
            if symbol_type not in by_type:
                by_type[symbol_type] = []
            by_type[symbol_type].append(symbol)
        
        # Generate examples for each type
        if 'class' in by_type:
            examples['class_examples'] = self._generate_class_examples(by_type['class'])
        
        if 'function' in by_type:
            examples['function_examples'] = self._generate_function_examples(by_type['function'])
        
        if relationships:
            examples['interaction_patterns'] = self._generate_interaction_examples(relationships)
        
        return examples
    
    def _generate_class_examples(self, classes: List[Dict[str, Any]]) -> str:
        """Generate class usage examples"""
        
        examples = ["# Relevant Classes in Codebase\n"]
        
        for cls in classes[:5]:
            examples.append(f"## {cls['symbol_name']}")
            examples.append(f"Location: {cls['file_path']}:{cls['line_start']}")
            examples.append(f"Type: {cls['symbol_type']}")
            examples.append("```python")
            examples.append(f"# Usage example for {cls['symbol_name']}")
            examples.append(f"from {self._extract_module_path(cls['file_path'])} import {cls['symbol_name']}")
            examples.append(f"")
            examples.append(f"# Initialize and use {cls['symbol_name']}")
            examples.append(f"instance = {cls['symbol_name']}()")
            examples.append("```\n")
        
        return "\n".join(examples)
    
    def _generate_function_examples(self, functions: List[Dict[str, Any]]) -> str:
        """Generate function usage examples"""
        
        examples = ["# Relevant Functions in Codebase\n"]
        
        for func in functions[:5]:
            examples.append(f"## {func['symbol_name']}")
            examples.append(f"Location: {func['file_path']}:{func['line_start']}")
            examples.append("```python")
            examples.append(f"# Call {func['symbol_name']}")
            examples.append(f"result = {func['symbol_name']}()")
            examples.append("```\n")
        
        return "\n".join(examples)
    
    def _generate_interaction_examples(self, relationships: List[Dict[str, Any]]) -> str:
        """Generate interaction pattern examples"""
        
        examples = ["# Code Interaction Patterns\n"]
        
        # Group by source function
        by_source = {}
        for rel in relationships[:10]:
            source = rel['source_symbol']
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(rel)
        
        for source, targets in list(by_source.items())[:3]:
            examples.append(f"## {source} calls:")
            for target in targets:
                examples.append(f"- {target['target_symbol']} ({target['file_path']}:{target['line_number']})")
            examples.append("")
        
        return "\n".join(examples)
    
    def _extract_module_path(self, file_path: str) -> str:
        """Extract Python module path from file path"""
        
        if '/app/' not in file_path:
            return "unknown_module"
        
        # Extract path after /app/
        app_index = file_path.find('/app/')
        if app_index == -1:
            return "unknown_module"
        
        module_path = file_path[app_index + 1:]  # Remove leading /
        module_path = module_path.replace('/', '.').replace('.py', '')
        
        return module_path
    
    def generate_dynamic_content(self, task_description: str, context_hints: List[str], 
                                role: str = "Dev") -> str:
        """Generate complete dynamic content for the given task and role"""
        
        self.logger.info("generating_dynamic_content", task=task_description[:100], role=role)
        
        # Extract keywords from task
        keywords = self.extract_task_keywords(task_description, context_hints)
        
        # Find relevant symbols
        symbols = self.find_relevant_symbols(keywords)
        
        # Find call relationships
        relationships = self.find_call_relationships(symbols)
        
        # Generate code examples
        examples = self.generate_code_examples(symbols, relationships)
        
        # Build complete dynamic content
        content_parts = [
            f"# Dynamic Context for {role} Role",
            f"Task: {task_description}",
            "",
            "## Relevant Keywords",
            ", ".join(sorted(list(keywords)[:15])),
            ""
        ]
        
        if symbols:
            content_parts.extend([
                "## Relevant Code Symbols",
                f"Found {len(symbols)} relevant symbols in codebase:",
                ""
            ])
            
            for symbol in symbols[:10]:
                content_parts.append(
                    f"- **{symbol['symbol_name']}** ({symbol['symbol_type']}) "
                    f"in {symbol['file_path']}:{symbol['line_start']} "
                    f"[relevance: {symbol['relevance_score']:.2f}]"
                )
        
        if relationships:
            content_parts.extend([
                "",
                "## Code Interactions",
                f"Found {len(relationships)} call relationships:",
                ""
            ])
            
            for rel in relationships[:8]:
                content_parts.append(
                    f"- {rel['source_symbol']} → {rel['target_symbol']} "
                    f"({rel['file_path']}:{rel['line_number']})"
                )
        
        # Add role-specific examples
        if examples:
            content_parts.append("\n## Code Examples\n")
            for example_type, example_content in examples.items():
                content_parts.append(example_content)
        
        # Add fallback content if no symbols found
        if not symbols and not relationships:
            content_parts.extend([
                "",
                "## Fallback Patterns",
                "No specific symbols found in index. Using general patterns:",
                "",
                "### Common FeatureFactory Patterns:",
                "- FastAPI endpoints in app/api/",
                "- SQLAlchemy models in app/db/models/",
                "- Pydantic schemas in app/api/schemas/",
                "- Tests in tests/ directory",
                "- Alembic migrations in app/db/migrations/versions/",
            ])
        
        final_content = "\n".join(content_parts)
        
        self.logger.info("dynamic_content_generated", 
                        content_length=len(final_content),
                        symbols_found=len(symbols),
                        relationships_found=len(relationships))
        
        return final_content

# Integration with ContextPackager
def integrate_dynamic_context(packager_instance, task_data: Dict[str, Any]) -> str:
    """Integration function to add dynamic content to ContextPackager"""
    
    engine = DynamicContextEngine()
    
    task_description = task_data.get('task', '')
    context_hints = task_data.get('context', [])
    role = task_data.get('role', 'Dev')
    
    if not task_description:
        return "# No task description available for dynamic context"
    
    return engine.generate_dynamic_content(task_description, context_hints, role)

# Example usage
if __name__ == "__main__":
    engine = DynamicContextEngine()
    
    # Example task
    sample_task = {
        'task': 'Create API endpoint for health checks with database connectivity test',
        'context': [
            '/opt/feature-factory/app/api/health.py',
            'FastAPI framework',
            'SQLAlchemy database'
        ],
        'role': 'Dev'
    }
    
    dynamic_content = integrate_dynamic_context(None, sample_task)
    print(dynamic_content)