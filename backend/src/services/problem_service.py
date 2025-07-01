"""
Problem Statement Analysis and Professor Matching Services

This module provides services for analyzing problem statements using Gemini AI
and matching professors based on the extracted research tags.

Key Components:
1. DatabaseService: Thread-safe MongoDB operations with connection pooling
2. MLService: Thread-safe ML operations with embedding caching
3. GeminiService: Service for problem statement analysis using Google's Gemini AI

Key Features:
- Thread-safe operations using RLock for all shared resources
- MongoDB connection pooling with configurable pool sizes
- Embedding caching with MD5 hash keys to avoid recomputation
- Comprehensive error handling and logging
"""

import logging
import threading
import google.generativeai as genai
import numpy as np
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class DatabaseService:
    """
    Thread-safe MongoDB service with connection pooling.
    
    Provides database operations for professor data with thread safety,
    connection pooling, and error handling.
    """
    
    def __init__(self, uri, db_name, collection_name, **mongo_options):
        """
        Initialize MongoDB connection with connection pooling.
        
        Args:
            uri (str): MongoDB connection URI
            db_name (str): Database name
            collection_name (str): Collection name
            **mongo_options: Additional MongoDB client options
        """
        self._lock = threading.RLock()
        self._client = None
        self._db = None
        self._collection = None
        self._uri = uri
        self._db_name = db_name
        self._collection_name = collection_name
        self._mongo_options = mongo_options
        
        # Initialize connection
        self._connect()
    
    def _connect(self):
        """Establish MongoDB connection with connection pooling"""
        with self._lock:
            try:
                if not self._client:
                    # Convert snake_case parameters to camelCase for MongoDB
                    camel_options = {}
                    for key, value in self._mongo_options.items():
                        # Handle specific parameters that need conversion
                        if key == "max_pool_size":
                            camel_options["maxPoolSize"] = value
                        elif key == "min_pool_size":
                            camel_options["minPoolSize"] = value
                        elif key == "server_selection_timeout":
                            camel_options["serverSelectionTimeoutMS"] = value
                        else:
                            # Keep other parameters as is
                            camel_options[key] = value
                    
                    self._client = MongoClient(self._uri, **camel_options)
                    self._db = self._client[self._db_name]
                    self._collection = self._db[self._collection_name]
                    
                    # Test connection
                    self._client.admin.command('ping')
                    logger.info("MongoDB connection established")
            except Exception as e:
                logger.error(f"MongoDB connection error: {str(e)}")
                raise
    
    def get_all_professors(self):
        """
        Retrieve all professors from the database.
        
        Returns:
            list: List of professor documents
        """
        with self._lock:
            try:
                return list(self._collection.find())
            except Exception as e:
                logger.error(f"Error retrieving professors: {str(e)}")
                return []


class MLService:
    """
    Thread-safe ML service for embedding and matching professors.
    
    Provides ML operations for embedding and matching professors based on
    research tags with thread safety, caching, and performance optimizations.
    """
    
    def __init__(self, model_name="all-MiniLM-L6-v2", batch_size=32, similarity_threshold=0.7):
        """
        Initialize ML service with embedding model.
        
        Args:
            model_name (str): SentenceTransformer model name
            batch_size (int): Batch size for embedding operations
            similarity_threshold (float): Threshold for tag similarity matching
        """
        self._lock = threading.RLock()
        self._model_name = model_name
        self._batch_size = batch_size
        self._similarity_threshold = similarity_threshold
        self._model = None
        
        # Professor data and embeddings
        self._professors_data = []
        self._prof_tag_embeddings = []
        self._prof_vector_means = []
        
        # Initialize model
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize SentenceTransformer model"""
        with self._lock:
            try:
                self._model = SentenceTransformer(self._model_name)
                logger.info(f"ML model '{self._model_name}' initialized")
            except Exception as e:
                logger.error(f"Error initializing ML model: {str(e)}")
                raise
    
    def initialize(self, professors):
        """
        Preprocess professor data and compute embeddings.
        
        Args:
            professors (list): List of professor documents from the database
        """
        with self._lock:
            try:
                # Process professor data
                prof_tags_list = []
                prof_details = []
                all_tags = []
                
                # Extract tags and details from each professor
                for prof in professors:
                    prof_extractions = prof.get("extractions", [])
                    if not prof_extractions or not any(extraction.get("tags") for extraction in prof_extractions):
                        continue
                    
                    # Collect tags and details
                    tags = []
                    pos_present = False
                    gid_present = False
                    
                    for extraction in prof_extractions:
                        tags.extend(extraction.get("tags", []))
                        if "position" in extraction:
                            prof_position = extraction["position"]
                            pos_present = True
                        if "google_scholar_id" in extraction:
                            prof_gs_id = extraction["google_scholar_id"]
                            gid_present = True
                    
                    if not pos_present:
                        prof_position = " "
                    if not gid_present:
                        prof_gs_id = ""
                    
                    # Remove duplicates
                    tags = list(set(tags))
                    
                    prof_tags_list.append(tags)
                    prof_details.append({
                        "_id": prof.get("_id", "Unknown"),
                        "department": prof.get("department", "Unknown"),
                        "base_url": prof.get("base_url", ""),
                        "position": prof_position,
                        "google_scholar_id": prof_gs_id
                    })
                    
                    all_tags.extend(tags)
                
                # Batch encode all tags for all professors
                if prof_tags_list:
                    # Flatten tags for batch encoding
                    flat_tags = [tag for tags in prof_tags_list for tag in tags]
                    flat_embeddings = self._model.encode(flat_tags, batch_size=self._batch_size, show_progress_bar=True)
                    emb_dim = flat_embeddings.shape[1]
                    
                    # Assign embeddings back to professors
                    idx = 0
                    for i, tags in enumerate(prof_tags_list):
                        n = len(tags)
                        tag_embs = flat_embeddings[idx:idx+n]
                        self._prof_tag_embeddings.append(tag_embs)
                        self._prof_vector_means.append(np.mean(tag_embs, axis=0))
                        idx += n
                    
                    # Build in-memory professor data
                    for idx, tags in enumerate(prof_tags_list):
                        if not tags:
                            continue
                        self._professors_data.append({
                            "_id": prof_details[idx].get("_id", "Unknown"),
                            "department": prof_details[idx].get("department", "Unknown"),
                            "base_url": prof_details[idx].get("base_url", ""),
                            "tags": tags,
                            "tag_embs": self._prof_tag_embeddings[idx],
                            "vector_mean": self._prof_vector_means[idx],
                            "position": prof_details[idx].get("position", ""),
                            "google_scholar_id": prof_details[idx].get("google_scholar_id", "")
                        })
                
                logger.info(f"Cached {len(self._professors_data)} professors in memory")
                
                # Store all unique tags
                self.all_tags = list(set(all_tags))
                
            except Exception as e:
                logger.error(f"Error preprocessing professor data: {str(e)}")
                raise
    
    def get_all_tags(self):
        """
        Get all unique research tags from professors.
        
        Returns:
            list: List of unique research tags
        """
        with self._lock:
            return sorted(set(self.all_tags))
    
    def find_professors(self, input_tags, weights, key_domain=None):
        """
        Find professors matching the input tags.
        
        Args:
            input_tags (list): List of research tags to match
            weights (list): List of weights corresponding to each input tag
            key_domain (dict): Domain importance mapping for departmental weighting
            
        Returns:
            list: List of matching professors with scores
        """
        with self._lock:
            if not input_tags:
                return []
            
            # Batch encode input tags
            input_embeddings = self._model.encode(input_tags)
            input_vector = np.average(input_embeddings, axis=0, weights=weights).reshape(1, -1)
            
            all_profs = []
            threshold = self._similarity_threshold
            
            for prof in self._professors_data:
                prof_name = prof["_id"]
                department = prof["department"]
                prof_tags = prof["tags"]
                prof_tag_embs = prof["tag_embs"]
                prof_vector = prof["vector_mean"].reshape(1, -1)
                
                # Semantic similarity
                sim_score = cosine_similarity(input_vector, prof_vector)[0][0]
                
                # Tag match logic (batch)
                matching_tags = []
                match_score = 0
                tag_scores = {}  # tag -> similarity score
                
                for i, tag in enumerate(input_tags):
                    tag_vec = input_embeddings[i].reshape(1, -1)
                    sim_scores = cosine_similarity(tag_vec, prof_tag_embs)[0]
                    
                    # Only consider this tag if at least one prof tag matches above threshold
                    matched_indices = np.where(sim_scores >= threshold)[0]
                    if matched_indices.size > 0:
                        for idx_match in matched_indices:
                            matching_tags.append(prof_tags[idx_match])
                        match_score += weights[i]
                        tag_scores[tag] = float(np.max(sim_scores))
                
                if not matching_tags:
                    continue  # Skip profs with no matches
                
                max_possible = np.sum(weights)
                weighted_score = (match_score / max_possible) * 100
                semantic_score = sim_score * 100
                rank_score = (semantic_score**2.1 + weighted_score**2)/2
                
                # Department-based weighting
                dept_score = 2.3
                if key_domain:
                    for domain, score in key_domain.items():
                        if domain.lower().split('(')[0].strip() in department.lower():
                            dept_score = float(score)
                            break
                    dept_weight = float(key_domain.get(department, 0.1))
                else:
                    dept_weight = 0.5
                
                rank_score = rank_score * (1 + dept_score * dept_weight)
                
                all_profs.append({
                    "name": prof_name,
                    "department": department,
                    "base_url": prof["base_url"],
                    "position": prof["position"],
                    "google_scholar_id": prof["google_scholar_id"],
                    "google_scholar_url": f"https://scholar.google.com/citations?user={prof['google_scholar_id']}&hl=en" if prof["google_scholar_id"] else "",
                    "semantic": round(semantic_score, 2),
                    "weighted_match": round(weighted_score, 2),
                    "rank_score": round(rank_score/100, 2),
                    "matching_tags": matching_tags,
                    "tag_scores": tag_scores 
                })
            
            # Sort all profs by rank_score descending
            top_profs = sorted(all_profs, key=lambda x: x["rank_score"], reverse=True)
            return top_profs


class GeminiService:
    """
    Service for analyzing problem statements using Gemini AI.
    
    Provides functionality to extract research tags and key domains from
    problem statements using Google's Gemini AI.
    """
    
    def __init__(self, api_key, model_name="gemini-2.0-flash"):
        """
        Initialize Gemini service.
        
        Args:
            api_key (str): Google API key for Gemini
            model_name (str): Gemini model name
        """
        self._lock = threading.RLock()
        self._api_key = api_key
        self._model_name = model_name
        self._model = None
        
        # Initialize Gemini
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Gemini AI with API key"""
        with self._lock:
            try:
                genai.configure(api_key=self._api_key)
                self._model = genai.GenerativeModel(self._model_name)
                logger.info(f"Gemini AI '{self._model_name}' initialized")
            except Exception as e:
                logger.error(f"Error initializing Gemini AI: {str(e)}")
                raise
    
    def extract_research_tags(self, problem_statement):
        """
        Extract research tags from a problem statement.
        
        Args:
            problem_statement (str): Problem statement text
            
        Returns:
            dict: Dictionary containing extracted tags, key domain, and explanation
        """
        with self._lock:
            try:
                prompt = f"""Analyze this research problem and extract the most precise and specific technical expertise areas (avoid redundant or overly broad terms; for example, do not include both 'machine learning' and 'deep learning'—choose the most specific and relevant one):

Problem: {problem_statement}

Return JSON with these keys:

"required_tags": array of the most precise, non-overlapping technical terms (max 8) in the order of importance.
"key_domain": Key domains required to solve the problem along with degree of importance of expertise from this area to solve the problem. The domains are to be chosen from [' Biochemistry (BC)', ' Central Animal Facility (CAF)', ' Centre for Ecological Sciences (CES)', ' Centre for Neuroscience (CNS)', ' Microbiology and Cell Biology (MCB)', ' Molecular Biophysics Unit (MBU)', ' Department of Developmental Biology and Genetics (DBG)', ' Inorganic and Physical Chemistry (IPC)', ' Materials Research Centre (MRC)', ' Organic Chemistry (OC)', ' Solid State and Structural Chemistry Unit (SSCU)', ' Computer Science and Automation (CSA)', ' Electrical Communication Engineering (ECE)', ' Electrical Engineering (EE)', ' Electronic Systems Engineering (ESE)', ' Centre for Infrastructure, Sustainable Transportation and Urban Planning (CiSTUP)', ' Department of Bioengineering (BE)', ' Centre for Society and Policy (CSP)', ' Centre for Nano Science and Engineering (CeNSE)', ' Computational and Data Sciences (CDS)', ' Management Studies (MS)', ' Supercomputer Education and Research Centre (SERC)', ' Aerospace Engineering (AE)', ' Centre for Atmospheric and Oceanic Sciences (CAOS)', ' Centre for Earth Sciences (CEaS)', ' Department of Design and Manufacturing (DM)', ' Centre for Sustainable Technologies (formerly known as ASTRA) (CST)', ' Chemical Engineering (CE)', ' Civil Engineering (CiE)', ' Divecha Centre for Climate Change (DCCC)', ' Materials Engineering (Mat. Eng.)', ' Mechanical Engineering (ME)', ' Astronomy and Astrophysics Programme (AAP)', ' Centre for High Energy Physics (CHEP)', ' Instrumentation and Applied Physics\xa0 (IAP)', ' Mathematics\xa0 (MA)', ' Physics (PHY)']
"explanation": A brief explanation of how the problem can be approached using the required tags.
Example output:
{{
"required_tags": ["remote sensing", "wildfire modeling", "convolutional neural networks"],
"key_domain": {{"data science": 0.9, "biology": 0.1}},
"explanation": "Remote sensing is needed for data acquisition, wildfire modeling for simulation, and CNNs for image analysis. Broader terms like 'machine learning' are omitted in favor of more precise tags."
}}

the key_domain should not miss any important domain. Eg: Dont skip 'Materials Engineering' just because 'Materials Research' is already included in the key_domain.
IMPORTANT: The required_tags should be specific - more of what a professor would list in their expertise.
Include ONLY the JSON with no additional text or markdown formatting."""

                # Generate response
                response = self._model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.2,
                        "max_output_tokens": 500
                    }
                )
                
                # Process and clean response
                json_str = response.text.strip()
                json_str = json_str.replace('```json', '').replace('```', '').strip()
                return json.loads(json_str)
                
            except Exception as e:
                logger.error(f"Error extracting tags: {str(e)}")
                return {
                    "required_tags": [],
                    "explanation": "Tag extraction failed"
                }
    
    def process_problem_statement(self, problem_statement):
        """
        Process a problem statement to extract tags and find matching professors.
        
        Args:
            problem_statement (str): Problem statement text
            ml_service (MLService): ML service for professor matching
            
        Returns:
            dict: Dictionary containing analysis results
        """
        # Extract tags and key domain
        gemini_result = self.extract_research_tags(problem_statement)
        return gemini_result
