"""
API Routes Module

This module defines all API endpoints for the Problem Statement Analysis application.
"""
from flask import Blueprint, request, jsonify, current_app
import numpy as np
from typing import List
import logging
import time
from functools import wraps
from difflib import SequenceMatcher

from ..services.problem_service import MLService, GeminiService
from ..utils.rate_limiter import ratelimit

logger = logging.getLogger(__name__)

# Create blueprint for API routes with URL prefix
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Global service instances (initialized in app factory)
ml_service: MLService = None
gemini_service: GeminiService = None

def init_routes(ml_service_instance: MLService, gemini_service_instance: GeminiService):
    """
    Initialize routes with service instances.
    
    Args:
        ml_service_instance (MLService): ML service for professor matching
        gemini_service_instance (GeminiService): Gemini service for problem statement analysis
    """
    global ml_service, gemini_service
    ml_service = ml_service_instance
    gemini_service = gemini_service_instance

@api_bp.route('/analyze', methods=['POST'])
@ratelimit(limit="30/minute")
def analyze_problem():
    """
    Analyze a problem statement and find suitable professors.
    
    Request:
        JSON with 'problem_statement' field
        
    Response:
        JSON with analysis results
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                "error": "Invalid request",
                "message": "Request must be JSON"
            }), 400
        
        data = request.get_json()
        problem_statement = data.get('problem_statement')
        mode = data.get('mode', 'team')  # 'team' or 'individual'
        
        if not problem_statement:
            return jsonify({
                "error": "Missing problem_statement",
                "message": "Problem statement is required"
            }), 400
        
        # Extract tags and key_domain using Gemini
        start_time = time.time()
        gemini_result = gemini_service.extract_research_tags(problem_statement)
        gemini_time = time.time() - start_time
        
        tags = gemini_result.get("required_tags", [])
        key_domain = gemini_result.get("key_domain", {})
        explanation = gemini_result.get("explanation", "")
        
        if not tags:
            return jsonify({
                "error": "Tag extraction failed",
                "message": "Failed to extract tags from problem statement"
            }), 500
        
        # Find professors matching the tags
        start_time = time.time()
        tag_weights = list(np.linspace(1.0, 0.7, num=len(tags)))
        results = ml_service.find_professors(tags, tag_weights, key_domain=key_domain)
        search_time = time.time() - start_time
        
        # Process professor matches for team formation
        # Map tags to professors
        tag_to_profs = {}
        prof_tag_score = {}  # (prof_name, tag) -> score
        prof_tag_rank_score = {}  # (prof_name) -> rank
        prof_coverage = {}  # prof_name -> set(tags)
        tag_groups = []  # For grouping similar tags
        tag_group_map = {}  # tag -> group_id
        group_id = 0
        
        # Build tag_to_profs and prof_coverage only for tags present in prof tag_scores
        for prof in results:
            prof_tag_rank_score[prof["name"]] = prof["rank_score"]
            
        for tag in tags:
            matching_profs = [prof for prof in results if tag in prof.get("tag_scores", {})]
            tag_to_profs[tag] = []
            
            if not matching_profs:
                continue
                
            for prof in matching_profs:
                tag_score = prof["tag_scores"][tag]
                tag_to_profs[tag].append({
                    "name": prof["name"],
                    "department": prof["department"],
                    "position": prof["position"],
                    "google_scholar_url": prof["google_scholar_url"],
                    "base_url": prof["base_url"],
                    "score": round(tag_score, 2)
                })
                prof_tag_score[(prof["name"], tag)] = tag_score
                prof_coverage.setdefault(prof["name"], set()).add(tag)
                
            # Sort by tag score (descending), then by rank score (descending)
            tag_to_profs[tag] = sorted(
                tag_to_profs[tag],
                key=lambda p: (
                    prof_tag_score.get((p["name"], tag), 0),      # tag expertise score
                    prof_tag_rank_score.get(p["name"], 0)         # overall rank score
                ),
                reverse=True
            )
            
        # Group similar tags (if their prof lists overlap a lot or tags are semantically similar)
        used = set()
        for i, tag1 in enumerate(tags):
            if tag1 in used:
                continue
            group = [tag1]
            for j, tag2 in enumerate(tags):
                if i == j or tag2 in used:
                    continue
                # Text similarity
                sim = SequenceMatcher(None, tag1, tag2).ratio()
                # Prof overlap
                profs1 = set(p['name'] for p in tag_to_profs.get(tag1, []))
                profs2 = set(p['name'] for p in tag_to_profs.get(tag2, []))
                overlap = len(profs1 & profs2) / (len(profs1 | profs2) + 1e-6)
                
                if sim > 0.8 or overlap > 0.9:
                    group.append(tag2)
                    used.add(tag2)
                    
            tag_groups.append(group)
            for t in group:
                tag_group_map[t] = group_id
            group_id += 1
            
        # Greedy set cover: select profs who cover most uncovered tags/groups
        uncovered = set(tags)
        team = []
        profs_used = set()
        
        while uncovered:
            # Find prof who covers most uncovered tags
            best_prof = None
            best_tags = set()
            prev_score_sum = 0
            
            for prof, covered_tags in prof_coverage.items():
                tags_left = set(covered_tags) & uncovered
                if not tags_left:
                    continue
                    
                # Sum tag scores for uncovered tags
                score_sum = sum(prof_tag_score.get((prof, tag), 0) for tag in tags_left)
                
                # Compare: prefer more tags, then higher score
                if (len(tags_left) > len(best_tags)) or (
                    len(tags_left) == len(best_tags) and (
                        best_prof is None or (score_sum > prev_score_sum or (
                            score_sum == prev_score_sum and 
                            prof_tag_rank_score.get(prof, 0) > prof_tag_rank_score.get(best_prof, 0)
                        ))
                    )
                ):
                    best_prof = prof
                    best_tags = tags_left
                    prev_score_sum = score_sum
                    
            if not best_prof:
                # No prof found for remaining tags
                break
                
            # Get professor details
            for p in results:
                if p["name"] == best_prof:
                    department = p["department"]
                    base_url = p["base_url"]
                    position = p["position"]
                    google_scholar_url = p["google_scholar_url"]
                    
            # Add to team
            team.append({
                "name": best_prof,
                "tags": list(best_tags),
                "department": department,
                "position": position,
                "base_url": base_url,
                "google_scholar_url": google_scholar_url
            })
            
            profs_used.add(best_prof)
            uncovered -= best_tags
            
        # For tags not covered, add not found
        not_found_tags = list(uncovered)
        
        # Mention grouping if any
        groupings = [g for g in tag_groups if len(g) > 1]
        grouping_message = ""
        if groupings:
            grouping_message = "Some input tags were grouped as they are very similar or can be handled by the same professor: "
            grouping_message += "  ".join(['(' + ", ".join(g) + ')' for g in groupings])
            
        # Prepare response
        response_data = {
            "tags": tags,
            "key_domain": key_domain,
            "explanation": explanation,
            "team": team,
            "individual": sorted(results, key=lambda x: x["rank_score"], reverse=True)[:20],  # Top 20 individual professors
            "all_profs_by_tag": tag_to_profs,
            "not_found_tags": not_found_tags,
            "grouping_message": grouping_message,
            "performance": {
                "gemini_time": round(gemini_time, 3),
                "search_time": round(search_time, 3),
                "total_time": round(gemini_time + search_time, 3)
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in analyze_problem: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@api_bp.route('/tags', methods=['GET'])
@ratelimit(limit="60/minute")
def get_tags():
    """
    Get all available tags from the database.
    
    Response:
        JSON with list of unique tags
    """
    try:
        unique_tags = ml_service.get_all_tags()
        return jsonify({"tags": unique_tags})
    except Exception as e:
        logger.error(f"Error in get_tags: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint.
    
    Response:
        JSON with service status
    """
    return jsonify({
        "status": "ok",
        "message": "Problem Statement Analysis API is running"
    })
