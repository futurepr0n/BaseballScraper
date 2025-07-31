#!/usr/bin/env python3
"""
Enhanced Player Name Matcher
Comprehensive name normalization and matching system for baseball players.
Handles accent characters, name format variations, and fuzzy matching.
"""

import unicodedata
import re
from typing import Dict, List, Optional, Set, Tuple
from difflib import SequenceMatcher, get_close_matches
import json

class PlayerNameNormalizer:
    """Advanced name normalization for baseball players"""
    
    def __init__(self):
        # Comprehensive accent mapping for manual fallback
        self.accent_map = {
            'á': 'a', 'à': 'a', 'ä': 'a', 'â': 'a', 'ā': 'a', 'ã': 'a',
            'é': 'e', 'è': 'e', 'ë': 'e', 'ê': 'e', 'ē': 'e',
            'í': 'i', 'ì': 'i', 'ï': 'i', 'î': 'i', 'ī': 'i',
            'ó': 'o', 'ò': 'o', 'ö': 'o', 'ô': 'o', 'ō': 'o', 'õ': 'o',
            'ú': 'u', 'ù': 'u', 'ü': 'u', 'û': 'u', 'ū': 'u',
            'ñ': 'n', 'ç': 'c', 'ß': 'ss',
            'Á': 'A', 'À': 'A', 'Ä': 'A', 'Â': 'A', 'Ā': 'A', 'Ã': 'A',
            'É': 'E', 'È': 'E', 'Ë': 'E', 'Ê': 'E', 'Ē': 'E',
            'Í': 'I', 'Ì': 'I', 'Ï': 'I', 'Î': 'I', 'Ī': 'I',
            'Ó': 'O', 'Ò': 'O', 'Ö': 'O', 'Ô': 'O', 'Ō': 'O', 'Õ': 'O',
            'Ú': 'U', 'Ù': 'U', 'Ü': 'U', 'Û': 'U', 'Ū': 'U',
            'Ñ': 'N', 'Ç': 'C'
        }
        
        # Common suffixes to handle
        self.suffixes = {'jr', 'sr', 'ii', 'iii', 'iv', 'v'}
        
        # Common Hispanic surnames for disambiguation
        self.common_hispanic_surnames = {
            'rodriguez', 'martinez', 'garcia', 'lopez', 'hernandez', 
            'gonzalez', 'perez', 'sanchez', 'ramirez', 'torres',
            'rivera', 'flores', 'morales', 'ortiz', 'vazquez',
            'jimenez', 'diaz', 'alvarez', 'castillo', 'mendoza'
        }
    
    def normalize_unicode(self, name: str) -> str:
        """Remove accents using Unicode normalization"""
        if not name:
            return ""
        
        # Method 1: Unicode NFD decomposition
        try:
            normalized = unicodedata.normalize('NFD', name)
            ascii_version = ''.join(
                char for char in normalized 
                if unicodedata.category(char) != 'Mn'  # Remove combining marks
            )
            return ascii_version
        except:
            # Method 2: Manual mapping fallback
            return ''.join(self.accent_map.get(char, char) for char in name)
    
    def normalize_name(self, name: str) -> str:
        """Comprehensive name normalization"""
        if not name:
            return ""
        
        # Step 1: Remove accents
        normalized = self.normalize_unicode(name)
        
        # Step 2: Clean special characters but preserve periods and hyphens
        cleaned = re.sub(r'[^\w\s\-\.]', '', normalized)
        
        # Step 3: Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def create_name_variants(self, full_name: str) -> Set[str]:
        """Generate all possible name variants for matching"""
        variants = set()
        
        if not full_name:
            return variants
        
        # Add original name (normalized)
        normalized = self.normalize_name(full_name)
        variants.add(normalized.lower())
        
        # Also add non-normalized version for exact matching
        variants.add(full_name.lower())
        
        # Parse name components
        parts = normalized.split()
        if len(parts) < 2:
            return variants
        
        # Handle suffixes
        suffix = None
        if parts[-1].lower().replace('.', '') in self.suffixes:
            suffix = parts[-1]
            parts = parts[:-1]
        
        if len(parts) >= 2:
            first = parts[0]
            last = parts[-1]
            middle = parts[1:-1] if len(parts) > 2 else []
            
            # Add basic variants
            variants.add(f"{first} {last}".lower())                           # First Last
            variants.add(f"{first[0]}. {last}".lower())                       # F. Last
            variants.add(last.lower())                                        # Last only
            
            # Add with middle names/initials
            if middle:
                middle_str = ' '.join(middle)
                middle_initials = ' '.join(f"{m[0]}." for m in middle)
                
                variants.add(f"{first} {middle_str} {last}".lower())          # First Middle Last
                variants.add(f"{first[0]}. {middle_initials} {last}".lower()) # F. M. Last
                variants.add(f"{first} {middle_initials} {last}".lower())     # First M. Last
            
            # Add with suffix if present
            if suffix:
                suffix_lower = suffix.lower()
                variants.add(f"{first} {last} {suffix_lower}".lower())
                variants.add(f"{first[0]}. {last} {suffix_lower}".lower())
                
                if middle:
                    middle_str = ' '.join(middle)
                    variants.add(f"{first} {middle_str} {last} {suffix_lower}".lower())
        
        # Add "Last, First" format variants
        if len(parts) >= 2:
            first = parts[0]
            last = parts[-1]
            variants.add(f"{last}, {first}".lower())                         # Last, First
            variants.add(f"{last}, {first[0]}.".lower())                     # Last, F.
        
        return variants
    
    def extract_key_components(self, name: str) -> Dict[str, str]:
        """Extract key name components for analysis"""
        normalized = self.normalize_name(name)
        parts = normalized.split()
        
        if not parts:
            return {}
        
        components = {'full_normalized': normalized.lower()}
        
        # Handle suffixes
        if parts[-1].lower().replace('.', '') in self.suffixes:
            components['suffix'] = parts[-1].lower()
            parts = parts[:-1]
        
        if len(parts) >= 1:
            components['last'] = parts[-1].lower()
        
        if len(parts) >= 2:
            components['first'] = parts[0].lower()
            components['first_initial'] = parts[0][0].lower()
        
        if len(parts) > 2:
            components['middle'] = ' '.join(parts[1:-1]).lower()
        
        return components

class PlayerNameMatcher:
    """Advanced player name matching with multiple algorithms"""
    
    def __init__(self):
        self.normalizer = PlayerNameNormalizer()
        self.cache = {}
    
    def calculate_similarity_score(self, name1: str, name2: str) -> float:
        """Calculate similarity score between two names using multiple methods"""
        if not name1 or not name2:
            return 0.0
        
        # Normalize both names
        norm1 = self.normalizer.normalize_name(name1).lower()
        norm2 = self.normalizer.normalize_name(name2).lower()
        
        # Exact match
        if norm1 == norm2:
            return 1.0
        
        # Sequence matcher
        seq_similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Component-based matching for better handling of name variations
        comp1 = self.normalizer.extract_key_components(name1)
        comp2 = self.normalizer.extract_key_components(name2)
        
        component_score = 0.0
        matches = 0
        total_components = 0
        
        # Compare key components
        for key in ['first', 'last', 'first_initial']:
            if key in comp1 and key in comp2:
                total_components += 1
                if comp1[key] == comp2[key]:
                    matches += 1
                    if key == 'last':  # Last name match is more important
                        component_score += 0.6
                    elif key == 'first':
                        component_score += 0.4
                    elif key == 'first_initial':
                        component_score += 0.3
        
        # If we have component matches, use component scoring
        if total_components > 0:
            component_similarity = min(component_score, 1.0)
            # Combine sequence and component similarity
            return max(seq_similarity, component_similarity)
        
        return seq_similarity
    
    def find_best_match(self, search_name: str, candidates: List[Dict], 
                       threshold: float = 0.7) -> Optional[Dict]:
        """Find best matching player from candidates"""
        if not search_name or not candidates:
            return None
        
        best_match = None
        best_score = 0.0
        best_method = 'none'
        
        # Create search variants
        search_variants = self.normalizer.create_name_variants(search_name)
        
        for candidate in candidates:
            candidate_names = []
            
            # Collect all possible names from candidate
            if candidate.get('fullName'):
                candidate_names.append(candidate['fullName'])
            if candidate.get('name'):
                candidate_names.append(candidate['name'])
                
            # Test each candidate name
            for candidate_name in candidate_names:
                if not candidate_name:
                    continue
                
                # Method 1: Exact variant match
                candidate_variants = self.normalizer.create_name_variants(candidate_name)
                if search_variants.intersection(candidate_variants):
                    score = 0.95
                    method = 'variant_match'
                else:
                    # Method 2: Similarity score
                    score = self.calculate_similarity_score(search_name, candidate_name)
                    method = 'similarity_match' if score >= threshold else 'low_similarity'
                
                if score > best_score:
                    best_match = {
                        'player': candidate,
                        'matched_name': candidate_name,
                        'search_name': search_name,
                        'score': score,
                        'method': method,
                        'confidence': min(score * 0.9, 0.95) if method == 'variant_match' else score * 0.8
                    }
                    best_score = score
        
        return best_match if best_score >= threshold else None
    
    def suggest_roster_improvements(self, api_name: str, roster_data: List[Dict]) -> List[Dict]:
        """Suggest improvements to roster data based on API name"""
        suggestions = []
        
        # Find potential matches that fell below threshold
        potential_matches = []
        for candidate in roster_data:
            candidate_names = [candidate.get('fullName', ''), candidate.get('name', '')]
            
            for candidate_name in candidate_names:
                if candidate_name:
                    score = self.calculate_similarity_score(api_name, candidate_name)
                    if 0.4 <= score < 0.7:  # Potential matches
                        potential_matches.append({
                            'player': candidate,
                            'candidate_name': candidate_name,
                            'score': score,
                            'api_name': api_name
                        })
        
        # Sort by score
        potential_matches.sort(key=lambda x: x['score'], reverse=True)
        
        # Generate suggestions for top potential matches
        for match in potential_matches[:3]:  # Top 3 suggestions
            player = match['player']
            
            # Suggest adding alternateNames field
            normalized_api = self.normalizer.normalize_name(api_name)
            
            suggestion = {
                'player_id': player.get('playerId', 'unknown'),
                'current_name': player.get('name', ''),
                'current_fullName': player.get('fullName', ''),
                'suggested_action': 'add_alternate_name',
                'suggested_value': normalized_api,
                'reason': f'API returned "{api_name}" which has {match["score"]:.2f} similarity to "{match["candidate_name"]}"',
                'confidence': match['score'],
                'team': player.get('team', '')
            }
            suggestions.append(suggestion)
        
        return suggestions

if __name__ == "__main__":
    # Test the enhanced matcher
    normalizer = PlayerNameNormalizer()
    matcher = PlayerNameMatcher()
    
    # Test cases
    test_cases = [
        ("Jasson Domínguez", "J. Dominguez"),
        ("Yandy Díaz", "Y. Diaz"),
        ("José Altuve", "J. Altuve"),
        ("Francisco Lindor", "F. Lindor"),
        ("Ronald Acuña Jr.", "R. Acuna"),
    ]
    
    print("🧪 Testing Enhanced Player Name Matcher")
    print("=" * 50)
    
    for api_name, roster_name in test_cases:
        print(f"\n🔍 Testing: '{api_name}' vs '{roster_name}'")
        
        # Test normalization
        norm_api = normalizer.normalize_name(api_name)
        norm_roster = normalizer.normalize_name(roster_name)
        print(f"   Normalized: '{norm_api}' vs '{norm_roster}'")
        
        # Test variants
        variants_api = normalizer.create_name_variants(api_name)
        variants_roster = normalizer.create_name_variants(roster_name)
        common_variants = variants_api.intersection(variants_roster)
        print(f"   Common variants: {len(common_variants)} found")
        if common_variants:
            print(f"   Examples: {list(common_variants)[:3]}")
        
        # Test similarity
        similarity = matcher.calculate_similarity_score(api_name, roster_name)
        print(f"   Similarity score: {similarity:.3f}")
        
        # Test matching
        mock_candidate = {
            'name': roster_name,
            'fullName': roster_name,
            'playerId': '12345',
            'team': 'TEST'
        }
        
        match_result = matcher.find_best_match(api_name, [mock_candidate])
        if match_result:
            print(f"   ✅ Match found: {match_result['method']} (confidence: {match_result['confidence']:.3f})")
        else:
            print(f"   ❌ No match found")
    
    print("\n🎯 Enhanced Player Name Matcher ready for integration!")