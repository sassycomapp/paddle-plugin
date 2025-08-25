"""
Test Data for Cache Management System.

This module provides test data for the cache management system,
including prompts, responses, embeddings, and other test fixtures.
"""

import json
import hashlib
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np
from datetime import datetime, timedelta


@dataclass
class TestPrompt:
    """Test prompt data structure."""
    id: str
    text: str
    category: str
    complexity: str  # "simple", "medium", "complex"
    expected_cache_layer: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TestResponse:
    """Test response data structure."""
    id: str
    prompt_id: str
    text: str
    cache_key: str
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TestUserSession:
    """Test user session data structure."""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    prompts: List[str] = None
    responses: List[str] = None
    
    def __post_init__(self):
        if self.prompts is None:
            self.prompts = []
        if self.responses is None:
            self.responses = []


class TestDataGenerator:
    """Test data generator for cache management system."""
    
    def __init__(self):
        self.test_prompts = []
        self.test_responses = []
        self.test_sessions = []
        self.embeddings = {}
        
        # Generate test data
        self._generate_test_prompts()
        self._generate_test_responses()
        self._generate_test_sessions()
        self._generate_embeddings()
    
    def _generate_test_prompts(self):
        """Generate test prompts for different categories."""
        prompt_categories = {
            "predictive": [
                "I'm going to ask about the weather tomorrow",
                "What will be the stock market performance next week?",
                "Can you predict the next trend in technology?",
                "I need help with my upcoming presentation",
                "What should I expect from the next product release?"
            ],
            "semantic": [
                "What is the meaning of life in philosophical terms?",
                "Explain the concept of artificial intelligence",
                "How does machine learning work?",
                "What are the principles of good software design?",
                "Describe the theory of relativity in simple terms"
            ],
            "vector": [
                "Find documents similar to machine learning algorithms",
                "Search for content about neural networks",
                "Retrieve information about deep learning architectures",
                "Find papers about natural language processing",
                "Search for content about computer vision techniques"
            ],
            "global": [
                "What are the SOLID principles in software design?",
                "Explain the difference between SQL and NoSQL databases",
                "What is the purpose of load balancing?",
                "How do microservices communicate with each other?",
                "What are the best practices for API design?"
            ],
            "vector_diary": [
                "Remember our conversation about yesterday's meeting",
                "What did we discuss about the project timeline?",
                "Recall the key points from our last discussion",
                "What decisions were made in our previous session?",
                "Summarize our conversation about budget constraints"
            ]
        }
        
        for category, prompts in prompt_categories.items():
            for i, prompt_text in enumerate(prompts):
                prompt_id = f"{category}_prompt_{i+1}"
                complexity = self._determine_complexity(prompt_text)
                
                prompt = TestPrompt(
                    id=prompt_id,
                    text=prompt_text,
                    category=category,
                    complexity=complexity,
                    expected_cache_layer=category,
                    metadata={
                        "created_at": datetime.now().isoformat(),
                        "word_count": len(prompt_text.split()),
                        "character_count": len(prompt_text)
                    }
                )
                
                self.test_prompts.append(prompt)
    
    def _generate_test_responses(self):
        """Generate test responses for prompts."""
        response_templates = {
            "predictive": [
                "Based on current trends and historical data, I predict that {topic} will show significant improvement in the near future.",
                "The forecast for {topic} indicates positive growth with a high probability of success.",
                "My analysis suggests that {topic} will experience substantial changes in the coming period."
            ],
            "semantic": [
                "The concept of {topic} refers to the fundamental principles that govern how {topic} operates and functions.",
                "In essence, {topic} represents a comprehensive framework for understanding and applying {topic} in various contexts.",
                "{topic} can be understood as a multifaceted approach that encompasses several key aspects including {aspects}."
            ],
            "vector": [
                "I found several relevant documents about {topic} that match your search criteria.",
                "The search returned {count} results related to {topic}, with varying levels of relevance.",
                "Here are the most relevant documents about {topic} based on semantic similarity."
            ],
            "global": [
                "{topic} is a fundamental concept in software development that involves {explanation}.",
                "The principles of {topic} are essential for creating robust and maintainable software systems.",
                "Understanding {topic} requires knowledge of several key concepts including {concepts}."
            ],
            "vector_diary": [
                "Based on our previous conversation about {topic}, we discussed several important points including {points}.",
                "Our last session covered {topic} in detail, focusing on {focus_areas}.",
                "From our previous discussion about {topic}, we established that {key_points}."
            ]
        }
        
        for prompt in self.test_prompts:
            # Generate response based on prompt category
            templates = response_templates.get(prompt.category, ["This is a response to your query."])
            template = np.random.choice(templates)
            
            # Customize response with prompt-specific content
            response_text = self._customize_response(template, prompt.text)
            
            # Generate cache key
            cache_key = hashlib.sha256(prompt.text.encode()).hexdigest()
            
            response = TestResponse(
                id=f"response_{prompt.id}",
                prompt_id=prompt.id,
                text=response_text,
                cache_key=cache_key,
                metadata={
                    "created_at": datetime.now().isoformat(),
                    "prompt_id": prompt.id,
                    "word_count": len(response_text.split()),
                    "character_count": len(response_text)
                }
            )
            
            self.test_responses.append(response)
    
    def _generate_test_sessions(self):
        """Generate test user sessions."""
        user_ids = ["user_1", "user_2", "user_3", "user_4", "user_5"]
        
        for user_id in user_ids:
            # Generate multiple sessions per user
            for session_num in range(1, 4):
                session_id = f"{user_id}_session_{session_num}"
                start_time = datetime.now() - timedelta(hours=session_num * 2)
                end_time = start_time + timedelta(minutes=30)
                
                # Select random prompts for this session
                session_prompts = np.random.choice(
                    [p.id for p in self.test_prompts if p.category in ["semantic", "vector_diary"]],
                    size=np.random.randint(3, 8),
                    replace=False
                )
                
                session_responses = []
                for prompt_id in session_prompts:
                    response = next(r for r in self.test_responses if r.prompt_id == prompt_id)
                    session_responses.append(response.id)
                
                session = TestUserSession(
                    session_id=session_id,
                    user_id=user_id,
                    start_time=start_time,
                    end_time=end_time,
                    prompts=session_prompts,
                    responses=session_responses
                )
                
                self.test_sessions.append(session)
    
    def _generate_embeddings(self):
        """Generate test embeddings for prompts and responses."""
        # Generate embeddings for prompts
        for prompt in self.test_prompts:
            embedding = self._generate_embedding(prompt.text, prompt.category)
            self.embeddings[prompt.id] = embedding
        
        # Generate embeddings for responses
        for response in self.test_responses:
            embedding = self._generate_embedding(response.text, response.id.split("_")[0])
            self.embeddings[response.id] = embedding
    
    def _determine_complexity(self, text: str) -> str:
        """Determine complexity level of text."""
        word_count = len(text.split())
        if word_count < 10:
            return "simple"
        elif word_count < 20:
            return "medium"
        else:
            return "complex"
    
    def _customize_response(self, template: str, prompt_text: str) -> str:
        """Customize response template with prompt-specific content."""
        # Extract key topics from prompt
        topics = self._extract_topics(prompt_text)
        
        # Replace template placeholders
        response = template
        for topic in topics:
            response = response.replace(f"{{{topic}}}", topic)
        
        # Add some randomness
        if "count" in response:
            count = np.random.randint(5, 15)
            response = response.replace("{count}", str(count))
        
        if "aspects" in response:
            aspects = ["theoretical foundations", "practical applications", "historical context"]
            response = response.replace("{aspects}", ", ".join(aspects))
        
        if "explanation" in response:
            explanation = "careful planning, systematic implementation, and continuous testing"
            response = response.replace("{explanation}", explanation)
        
        if "concepts" in response:
            concepts = ["abstraction", "encapsulation", "inheritance", "polymorphism"]
            response = response.replace("{concepts}", ", ".join(concepts))
        
        if "points" in response:
            points = ["key decisions", "action items", "next steps", "resource allocation"]
            response = response.replace("{points}", ", ".join(points))
        
        if "focus_areas" in response:
            focus_areas = ["technical requirements", "timeline management", "budget considerations"]
            response = response.replace("{focus_areas}", ", ".join(focus_areas))
        
        if "key_points" in response:
            key_points = "clear objectives, defined milestones, and measurable outcomes"
            response = response.replace("{key_points}", key_points)
        
        return response
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract key topics from text."""
        # Simple topic extraction based on keywords
        topic_keywords = {
            "weather": ["weather", "forecast", "temperature", "climate"],
            "stock": ["stock", "market", "finance", "investment"],
            "technology": ["technology", "tech", "innovation", "digital"],
            "presentation": ["presentation", "slides", "talk", "speech"],
            "product": ["product", "release", "launch", "version"],
            "philosophy": ["philosophy", "meaning", "existence", "purpose"],
            "ai": ["artificial intelligence", "AI", "machine learning", "neural"],
            "software": ["software", "code", "programming", "development"],
            "database": ["database", "SQL", "NoSQL", "storage"],
            "microservices": ["microservices", "service", "architecture", "distributed"]
        }
        
        topics = []
        for topic, keywords in topic_keywords.items():
            if any(keyword in text.lower() for keyword in keywords):
                topics.append(topic)
        
        return topics if topics else ["general"]
    
    def _generate_embedding(self, text: str, category: str) -> List[float]:
        """Generate test embedding for text."""
        # Generate pseudo-random embedding based on text and category
        np.random.seed(hash(text + category) % 2**32)
        embedding = np.random.randn(384).tolist()  # 384 dimensions like OpenAI embeddings
        
        # Add some category-specific patterns
        if category == "semantic":
            # Add semantic pattern
            embedding[0] = 0.8
            embedding[1] = 0.6
        elif category == "vector":
            # Add vector pattern
            embedding[2] = 0.9
            embedding[3] = 0.7
        elif category == "predictive":
            # Add predictive pattern
            embedding[4] = 0.7
            embedding[5] = 0.8
        
        return embedding
    
    def get_test_prompts(self, category: Optional[str] = None, complexity: Optional[str] = None) -> List[TestPrompt]:
        """Get test prompts filtered by category and complexity."""
        prompts = self.test_prompts
        
        if category:
            prompts = [p for p in prompts if p.category == category]
        
        if complexity:
            prompts = [p for p in prompts if p.complexity == complexity]
        
        return prompts
    
    def get_test_responses(self, prompt_id: Optional[str] = None) -> List[TestResponse]:
        """Get test responses, optionally filtered by prompt ID."""
        if prompt_id:
            return [r for r in self.test_responses if r.prompt_id == prompt_id]
        return self.test_responses
    
    def get_test_sessions(self, user_id: Optional[str] = None) -> List[TestUserSession]:
        """Get test sessions, optionally filtered by user ID."""
        if user_id:
            return [s for s in self.test_sessions if s.user_id == user_id]
        return self.test_sessions
    
    def get_embeddings(self, item_id: Optional[str] = None) -> Dict[str, List[float]]:
        """Get embeddings, optionally for a specific item."""
        if item_id:
            return {item_id: self.embeddings.get(item_id)}
        return self.embeddings
    
    def get_similar_prompts(self, prompt_text: str, n_results: int = 5) -> List[TestPrompt]:
        """Get similar prompts based on text similarity."""
        # Simple similarity based on shared words
        target_words = set(prompt_text.lower().split())
        
        similarities = []
        for prompt in self.test_prompts:
            prompt_words = set(prompt.text.lower().split())
            similarity = len(target_words.intersection(prompt_words)) / len(target_words.union(prompt_words))
            similarities.append((prompt, similarity))
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [prompt for prompt, _ in similarities[:n_results]]
    
    def generate_test_scenario(self, scenario_type: str) -> Dict[str, Any]:
        """Generate a specific test scenario."""
        if scenario_type == "conversation":
            return self._generate_conversation_scenario()
        elif scenario_type == "multi_session":
            return self._generate_multi_session_scenario()
        elif scenario_type == "high_frequency":
            return self._generate_high_frequency_scenario()
        elif scenario_type == "mixed_cache_layers":
            return self._generate_mixed_cache_scenario()
        else:
            raise ValueError(f"Unknown scenario type: {scenario_type}")
    
    def _generate_conversation_scenario(self) -> Dict[str, Any]:
        """Generate a conversation test scenario."""
        # Select a user session
        session = np.random.choice(self.test_sessions)
        
        # Get prompts and responses for this session
        session_prompts = [p for p in self.test_prompts if p.id in session.prompts]
        session_responses = [r for r in self.test_responses if r.id in session.responses]
        
        return {
            "scenario_type": "conversation",
            "session_id": session.session_id,
            "user_id": session.user_id,
            "prompts": [asdict(p) for p in session_prompts],
            "responses": [asdict(r) for r in session_responses],
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None
        }
    
    def _generate_multi_session_scenario(self) -> Dict[str, Any]:
        """Generate a multi-session test scenario."""
        # Select a user with multiple sessions
        user_sessions = [s for s in self.test_sessions if s.user_id == "user_1"]
        
        if len(user_sessions) < 2:
            # Fallback to any user with multiple sessions
            user_sessions = [s for s in self.test_sessions if len([ss for ss in self.test_sessions if ss.user_id == s.user_id]) > 1]
            user_sessions = np.random.choice(user_sessions, size=min(3, len(user_sessions)), replace=False)
        else:
            user_sessions = np.random.choice(user_sessions, size=min(3, len(user_sessions)), replace=False)
        
        # Get all prompts and responses for these sessions
        all_prompts = []
        all_responses = []
        
        for session in user_sessions:
            session_prompts = [p for p in self.test_prompts if p.id in session.prompts]
            session_responses = [r for r in self.test_responses if r.id in session.responses]
            
            all_prompts.extend(session_prompts)
            all_responses.extend(session_responses)
        
        return {
            "scenario_type": "multi_session",
            "user_id": user_sessions[0].user_id,
            "sessions": [asdict(s) for s in user_sessions],
            "total_prompts": len(all_prompts),
            "total_responses": len(all_responses),
            "prompts": [asdict(p) for p in all_prompts],
            "responses": [asdict(r) for r in all_responses]
        }
    
    def _generate_high_frequency_scenario(self) -> Dict[str, Any]:
        """Generate a high-frequency request scenario."""
        # Select popular prompts (those that appear in multiple sessions)
        prompt_counts = {}
        for session in self.test_sessions:
            for prompt_id in session.prompts:
                prompt_counts[prompt_id] = prompt_counts.get(prompt_id, 0) + 1
        
        # Get most frequent prompts
        popular_prompts = sorted(prompt_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        popular_prompt_ids = [pid for pid, _ in popular_prompts]
        
        # Get full prompt objects
        popular_prompts = [p for p in self.test_prompts if p.id in popular_prompt_ids]
        
        return {
            "scenario_type": "high_frequency",
            "popular_prompts": [asdict(p) for p in popular_prompts],
            "request_frequencies": {pid: count for pid, count in popular_prompts},
            "total_unique_prompts": len(popular_prompts),
            "total_requests": sum(count for _, count in popular_prompts)
        }
    
    def _generate_mixed_cache_scenario(self) -> Dict[str, Any]:
        """Generate a mixed cache layer scenario."""
        # Select prompts from different cache layers
        layer_prompts = {}
        for category in ["predictive", "semantic", "vector", "global", "vector_diary"]:
            prompts = self.get_test_prompts(category=category)
            layer_prompts[category] = prompts[:2]  # Take 2 prompts from each layer
        
        # Flatten all prompts
        all_prompts = []
        for category, prompts in layer_prompts.items():
            all_prompts.extend(prompts)
        
        # Get corresponding responses
        all_responses = []
        for prompt in all_prompts:
            response = next(r for r in self.test_responses if r.prompt_id == prompt.id)
            all_responses.append(response)
        
        return {
            "scenario_type": "mixed_cache_layers",
            "prompts_by_layer": {
                category: [asdict(p) for p in prompts]
                for category, prompts in layer_prompts.items()
            },
            "total_prompts": len(all_prompts),
            "total_responses": len(all_responses),
            "prompts": [asdict(p) for p in all_prompts],
            "responses": [asdict(r) for r in all_responses]
        }
    
    def export_test_data(self, output_file: str):
        """Export test data to JSON file."""
        test_data = {
            "prompts": [asdict(p) for p in self.test_prompts],
            "responses": [asdict(r) for r in self.test_responses],
            "sessions": [asdict(s) for s in self.test_sessions],
            "embeddings": self.embeddings,
            "generated_at": datetime.now().isoformat(),
            "total_prompts": len(self.test_prompts),
            "total_responses": len(self.test_responses),
            "total_sessions": len(self.test_sessions),
            "total_embeddings": len(self.embeddings)
        }
        
        with open(output_file, 'w') as f:
            json.dump(test_data, f, indent=2, default=str)
        
        return output_file


# Global test data instance
TEST_DATA = TestDataGenerator()


def get_test_data() -> TestDataGenerator:
    """Get the global test data instance."""
    return TEST_DATA


def create_test_data_file(output_file: str = "test_data.json"):
    """Create a test data file."""
    test_data = TestDataGenerator()
    return test_data.export_test_data(output_file)


if __name__ == "__main__":
    # Create test data file
    data_file = create_test_data_file()
    print(f"Test data file created: {data_file}")
    
    # Display test data summary
    test_data = get_test_data()
    print(f"Generated {len(test_data.test_prompts)} prompts")
    print(f"Generated {len(test_data.test_responses)} responses")
    print(f"Generated {len(test_data.test_sessions)} sessions")
    print(f"Generated {len(test_data.embeddings)} embeddings")
    
    # Display sample data
    print("\nSample prompts:")
    for i, prompt in enumerate(test_data.test_prompts[:3]):
        print(f"{i+1}. {prompt.text} (Category: {prompt.category}, Complexity: {prompt.complexity})")
    
    print("\nSample responses:")
    for i, response in enumerate(test_data.test_responses[:3]):
        prompt = next(p for p in test_data.test_prompts if p.id == response.prompt_id)
        print(f"{i+1}. Response to: {prompt.text}")
        print(f"   Response: {response.text}")