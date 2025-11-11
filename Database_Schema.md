# IndiByte Database Schema

[[Project_IndiByte_Structured]] ← Back to Project Overview
[[IndiByte_PRD]] ← Back to PRD
[[API Documentation]] ← Back to API Docs

---

## Table of Contents
- [Overview](#overview)
- [Database Design Principles](#database-design-principles)
- [Core Collections/Tables](#core-collectionstables)
- [Food Collection Schema](#food-collection-schema)
- [User Collection Schema](#user-collection-schema)
- [Nutrition Log Collection Schema](#nutrition-log-collection-schema)
- [Recommendation Collection Schema](#recommendation-collection-schema)
- [Community Contribution Schema](#community-contribution-schema)
- [Regional Data Schema](#regional-data-schema)
- [Medical Validation Schema](#medical-validation-schema)
- [API Usage Schema](#api-usage-schema)
- [Indexes and Performance](#indexes-and-performance)
- [Relationships](#relationships)
- [Data Validation Rules](#data-validation-rules)

---

## Overview

The IndiByte database schema is designed to store comprehensive information about Indian foods, their nutritional content, cultural context, and related user data. The schema supports the core functionality of the platform including food search, personalized recommendations, and community contributions.

### Database Type
- **Primary**: NoSQL (MongoDB) for flexible schema handling
- **Secondary**: PostgreSQL for transactional data and user management

### Design Goals
- Support flexible food data with varying attributes
- Enable efficient search and filtering
- Maintain data integrity for medical information
- Support Indian regional variations
- Enable community contributions with validation

---

## Database Design Principles

### 1. Flexibility First
- Schema allows for varying nutritional attributes across different food types
- Accommodates regional names and preparation methods for the same food
- Supports multiple measurement units and serving sizes

### 2. Indian-Centric Design
- Special fields for Indian food categories (e.g., pulse, grain, spice)
- Regional variation tracking within single food entries
- Cultural context and dietary restriction information

### 3. Medical Accuracy
- All medical claims linked to ICMR-validated sources
- Clear distinction between nutritional facts and medical recommendations
- Audit trail for all health-related data changes

### 4. Community-Oriented
- Contribution tracking and validation workflows
- Multiple source verification for food data
- Transparent data quality metrics

---

## Core Collections/Tables

### MongoDB Collections
1. `foods` - Main food database
2. `users` - User profiles and preferences
3. `nutrition_logs` - User food intake tracking
4. `recommendations` - Generated recommendations
5. `contributions` - Community contributions
6. `validations` - Medical validation records
7. `regional_data` - Regional food variations
8. `api_usage` - API usage tracking

### PostgreSQL Tables
1. `user_accounts` - User authentication
2. `api_keys` - API key management
3. `health_conditions` - Medical condition reference
4. `dietary_restrictions` - Dietary restriction reference

---

## Food Collection Schema

The `foods` collection stores all food items in the IndiByte database.

```json
{
  "_id": ObjectId,
  "food_id": "unique_food_identifier",
  "primary_name": "string (required)",
  "names": {
    "local": ["string"],
    "regional": {
      "hindi": "string",
      "bengali": "string", 
      "tamil": "string",
      "telugu": "string",
      "marathi": "string",
      "gujarati": "string",
      "punjabi": "string",
      "kannada": "string",
      "malayalam": "string"
    },
    "scientific": "string",
    "english": "string"
  },
  "category": {
    "primary": "enum(grain, pulse, vegetable, fruit, spice, herb, dairy, meat, fish, egg, oil, sweet)",
    "secondary": ["string"],
    "dietary_type": ["vegetarian", "vegan", "non_vegetarian", "jain", "halal", "kosher"]
  },
  "nutrition": {
    "per_100g": {
      "calories": "number",
      "protein_g": "number",
      "carbs_g": "number", 
      "fats_g": "number",
      "fiber_g": "number",
      "sugar_g": "number",
      "sodium_mg": "number",
      "cholesterol_mg": "number",
      "saturated_fat_g": "number",
      "trans_fat_g": "number"
    },
    "vitamins": {
      "a_iu": "number",
      "b1_thiamin_mg": "number", 
      "b2_riboflavin_mg": "number",
      "b3_niacin_mg": "number",
      "b5_pantothenic_mg": "number",
      "b6_mg": "number",
      "b12_mcg": "number",
      "c_mg": "number",
      "d_iu": "number",
      "e_mg": "number",
      "k_mcg": "number",
      "folate_mcg": "number"
    },
    "minerals": {
      "calcium_mg": "number",
      "iron_mg": "number",
      "magnesium_mg": "number",
      "phosphorus_mg": "number",
      "potassium_mg": "number",
      "sodium_mg": "number",
      "zinc_mg": "number",
      "copper_mg": "number",
      "manganese_mg": "number",
      "selenium_mcg": "number",
      "fluoride_mcg": "number",
      "iodine_mcg": "number"
    }
  },
  "cultural_context": {
    "regional_prevalence": "string",
    "traditional_use": "string",
    "religious_significance": "string",
    "seasonal_consumption": "string",
    "cooking_methods": ["string"]
  },
  "economic_data": {
    "price_per_kg": "number",
    "price_currency": "string (default: INR)",
    "regional_price_variation": {
      "north": "number",
      "south": "number", 
      "east": "number",
      "west": "number"
    },
    "affordability_index": "number (1-10 scale)"
  },
  "medical_considerations": {
    "beneficial_for": [
      {
        "condition": "string",
        "validation_source": "string (ICMR reference)",
        "evidence_level": "string (high/moderate/low)",
        "notes": "string"
      }
    ],
    "conditions_to_avoid": [
      {
        "condition": "string", 
        "severity": "string (mild/moderate/severe)",
        "validation_source": "string",
        "notes": "string"
      }
    ],
    "allergens": ["string"],
    "drug_interactions": [
      {
        "medication_class": "string",
        "interaction_type": "string",
        "medical_advice": "string"
      }
    ],
    "digestive_impact": {
      "gas_production": "string (low/medium/high)",
      "digestibility": "string (easy/moderate/difficult)",
      "acidity_level": "string (acidic/neutral/alkaline)"
    }
  },
  "preparation_methods": [
    {
      "method_name": "string",
      "regional_variations": ["string"],
      "nutritional_changes": "string",
      "health_impact": "string"
    }
  ],
  "regional_variations": [
    {
      "region": "string",
      "preparation_style": "string",
      "ingredient_variations": ["string"],
      "cultural_significance": "string"
    }
  ],
  "tags": ["string"],
  "metadata": {
    "created_by": "user_id",
    "created_at": "ISODate",
    "updated_by": "user_id", 
    "updated_at": "ISODate",
    "icmr_verified": "boolean",
    "icmr_verification_date": "ISODate",
    "icmr_verification_source": "string",
    "data_quality_score": "number (0-100)",
    "community_contributions_count": "number",
    "last_community_update": "ISODate"
  }
}
```

### Example Document
```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "food_id": "rohu-fish-bengali",
  "primary_name": "Rohu Fish",
  "names": {
    "local": ["Rui", "Thai Thailla"],
    "regional": {
      "hindi": "रुहु",
      "bengali": "রুই",
      "tamil": "அண்ணாசு மீன்", 
      "telugu": "రొహు చేప",
      "marathi": "राहू माहीत",
      "gujarati": "રોહુ",
      "punjabi": "ਰੂਹੂ",
      "kannada": "ರೊಹು",
      "malayalam": "അണ്ണാസ് മത്സ്യം"
    },
    "scientific": "Labeo rohita",
    "english": "Rohu Fish"
  },
  "category": {
    "primary": "fish",
    "secondary": ["freshwater", "cyprinidae"],
    "dietary_type": ["non_vegetarian"]
  },
  "nutrition": {
    "per_100g": {
      "calories": 120,
      "protein_g": 22.0,
      "carbs_g": 0,
      "fats_g": 3.5,
      "fiber_g": 0,
      "sugar_g": 0,
      "sodium_mg": 59,
      "cholesterol_mg": 60,
      "saturated_fat_g": 0.8,
      "trans_fat_g": 0
    },
    "vitamins": {
      "b12_mcg": 2.5,
      "d_iu": 5.0,
      "niacin_mg": 4.5
    },
    "minerals": {
      "phosphorus_mg": 210,
      "potassium_mg": 340,
      "selenium_mcg": 25.5,
      "iron_mg": 0.8
    }
  },
  "cultural_context": {
    "regional_prevalence": "High in Bengal, Bihar, Odisha, Uttar Pradesh",
    "traditional_use": "Essential for Bengali cuisine, especially during festivities",
    "religious_significance": "Considered auspicious for Bengali weddings and Pujas",
    "seasonal_consumption": "Available year-round, peak season during monsoons",
    "cooking_methods": [
      "Mustard gravy preparation", 
      "Fried with turmeric and salt",
      "In fish curry with yogurt"
    ]
  },
  "economic_data": {
    "price_per_kg": 120,
    "price_currency": "INR",
    "regional_price_variation": {
      "north": 120,
      "south": 150,
      "east": 100,
      "west": 140
    },
    "affordability_index": 7
  },
  "medical_considerations": {
    "beneficial_for": [
      {
        "condition": "cardiovascular_health",
        "validation_source": "ICMR-NIN-2023-001",
        "evidence_level": "high",
        "notes": "Rich in omega-3 fatty acids"
      },
      {
        "condition": "brain_function",
        "validation_source": "ICMR-NIN-2023-002",
        "evidence_level": "moderate",
        "notes": "High protein supports cognitive function"
      }
    ],
    "conditions_to_avoid": [
      {
        "condition": "gout",
        "severity": "moderate",
        "validation_source": "ICMR-GOUT-2022-001",
        "notes": "High purine content may trigger gout"
      },
      {
        "condition": "fish_allergy",
        "severity": "severe",
        "validation_source": "ICMR-ALLERGY-2022-001",
        "notes": "Common fish allergen"
      }
    ],
    "allergens": ["fish"],
    "drug_interactions": [
      {
        "medication_class": "blood_thinners",
        "interaction_type": "potentiates_anticoagulant_effects",
        "medical_advice": "Monitor INR levels if consuming regularly with warfarin"
      }
    ],
    "digestive_impact": {
      "gas_production": "low",
      "digestibility": "easy",
      "acidity_level": "neutral"
    }
  },
  "preparation_methods": [
    {
      "method_name": "Bengali Mustard Gravy",
      "regional_variations": ["Bengal: with poppy seeds", "Odisha: with paanch phoron"],
      "nutritional_changes": "Adds 15-20 calories from mustard oil",
      "health_impact": "Mustard provides antioxidants"
    }
  ],
  "regional_variations": [
    {
      "region": "Bengal",
      "preparation_style": "Jhol with mustard and poppy seeds",
      "ingredient_variations": ["Mustard oil instead of other oils", "Paanch phoron whole spices"],
      "cultural_significance": "Essential for Bengali Saturday lunches"
    }
  ],
  "tags": ["omega_3_rich", "high_protein", "gout_caution", "bengali_staple", "puja_significance"],
  "metadata": {
    "created_by": "admin",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_by": "medical_reviewer_001",
    "updated_at": "2025-10-22T14:45:00Z",
    "icmr_verified": true,
    "icmr_verification_date": "2025-10-22T14:45:00Z",
    "icmr_verification_source": "ICMR-NIN-FISH-NUTRITION-2025",
    "data_quality_score": 95,
    "community_contributions_count": 12,
    "last_community_update": "2025-11-05T09:15:00Z"
  }
}
```

---

## User Collection Schema

The `users` collection stores user preferences, health information, and personalization data.

```json
{
  "_id": ObjectId,
  "user_id": "unique_user_identifier",
  "profile": {
    "name": "string",
    "age": "number",
    "gender": "enum(male, female, other, prefer_not_to_say)",
    "height_cm": "number",
    "weight_kg": "number",
    "location": {
      "city": "string",
      "state": "string",
      "pin_code": "string",
      "region_preference": "string"
    }
  },
  "health_information": {
    "medical_conditions": [
      {
        "condition": "string",
        "diagnosis_date": "ISODate",
        "severity": "string (mild/moderate/severe)",
        "medications": ["string"],
        "medical_supervisor": "string (doctor_id)"
      }
    ],
    "allergies": [
      {
        "substance": "string",
        "reaction_type": "string",
        "severity": "string",
        "last_reaction_date": "ISODate"
      }
    ],
    "dietary_restrictions": ["string (vegetarian, vegan, gluten_free, etc.)"],
    "religious_dietary_laws": ["string (halal, Jain, etc.)"]
  },
  "preferences": {
    "cuisine_preference": ["string"],
    "flavor_profiles": ["sweet", "spicy", "sour", "bitter", "astringent"],
    "cooking_skill_level": "enum(novice, beginner, intermediate, advanced, expert)",
    "budget_constraints": {
      "max_spending_per_meal": "number",
      "currency": "string",
      "budget_flexibility": "enum(strict, moderate, flexible)"
    },
    "food_preferences": {
      "liked_foods": ["food_id"],
      "disliked_foods": ["food_id"],
      "foods_to_avoid": ["food_id"]
    }
  },
  "history": {
    "food_log": [
      {
        "date": "ISODate",
        "meal_type": "enum(breakfast, lunch, dinner, snack)",
        "foods_consumed": [
          {
            "food_id": "string",
            "quantity_g": "number",
            "satisfaction_rating": "number (1-5)"
          }
        ],
        "total_calories": "number",
        "total_protein": "number"
      }
    ],
    "recommendations_viewed": [
      {
        "recommendation_id": "string",
        "viewed_at": "ISODate",
        "followed": "boolean",
        "feedback": "string"
      }
    ]
  },
  "goals": [
    {
      "goal_type": "string (weight_loss, muscle_gain, diabetes_management, etc.)",
      "target": "string",
      "timeframe_days": "number",
      "current_progress": "number"
    }
  ],
  "integration_preferences": [
    {
      "platform": "string (zomato, swiggy, etc.)",
      "enabled": "boolean",
      "settings": "object"
    }
  ],
  "metadata": {
    "account_created_at": "ISODate",
    "last_active": "ISODate",
    "api_key": "string",
    "consent_for_data_sharing": "boolean",
    "notification_preferences": {
      "email": "boolean",
      "sms": "boolean",
      "push": "boolean"
    }
  }
}
```

---

## Nutrition Log Collection Schema

The `nutrition_logs` collection stores detailed daily nutrition logs for users.

```json
{
  "_id": ObjectId,
  "log_id": "unique_log_identifier",
  "user_id": "string",
  "date": "ISODate",
  "meal_type": "enum(breakfast, lunch, dinner, snack)",
  "foods_consumed": [
    {
      "food_id": "string",
      "food_name": "string",
      "quantity_g": "number",
      "serving_unit": "string (e.g., 'piece', 'bowl', 'cup')",
      "serving_size": "number",
      "nutrition_breakdown": {
        "calories": "number",
        "protein": "number",
        "carbs": "number",
        "fats": "number",
        "fiber": "number",
        "sodium": "number",
        "vitamins": "object",
        "minerals": "object"
      }
    }
  ],
  "meal_rating": "number (1-5)",
  "meal_photo_url": "string",
  "notes": "string",
  "meal_time": "string (HH:MM format)",
  "total_nutrition": {
    "calories": "number",
    "protein_g": "number",
    "carbs_g": "number", 
    "fats_g": "number",
    "fiber_g": "number",
    "sodium_mg": "number"
  },
  "health_metrics_post_meal": {
    "blood_sugar_level": "number (if diabetic)",
    "digestive_comfort": "number (1-5)",
    "energy_level": "number (1-5)"
  },
  "metadata": {
    "created_at": "ISODate",
    "updated_at": "ISODate",
    "source": "enum(mobile_app, web_app, integration, manual_entry)"
  }
}
```

---

## Recommendation Collection Schema

The `recommendations` collection stores personalized recommendations generated for users.

```json
{
  "_id": ObjectId,
  "recommendation_id": "unique_recommendation_id",
  "user_id": "string",
  "generation_timestamp": "ISODate",
  "recommendation_type": "enum(personalized_meal, recipe_suggestion, health_alert, nutritional_gap_filler)",
  "meal_type": "enum(breakfast, lunch, dinner, snack, anytime)",
  "target_nutrition": {
    "calories": "number (range)",
    "protein_g": "number (range)",
    "carbs_g": "number (range)",
    "fats_g": "number (range)"
  },
  "recommended_items": [
    {
      "item_id": "string",
      "item_name": "string",
      "item_type": "enum(food, recipe, meal_plan)",
      "relevance_score": "number (0-1)",
      "cultural_alignment_score": "number (0-1)",
      "health_alignment_score": "number (0-1)",
      "cost_estimate": {
        "amount": "number",
        "currency": "string"
      },
      "preparation_time_minutes": "number",
      "serving_size": "string",
      "cooking_difficulty": "enum(easy, moderate, difficult)",
      "ingredients": [
        {
          "food_id": "string",
          "quantity_g": "number"
        }
      ],
      "nutrition_per_serving": {
        "calories": "number",
        "protein_g": "number",
        "carbs_g": "number",
        "fats_g": "number"
      },
      "health_considerations": [
        {
          "condition": "string (e.g., diabetes_friendly)",
          "benefit": "string",
          "evidence_level": "string"
        }
      ]
    }
  ],
  "alternative_items": [
    {
      "item_id": "string",
      "reason_for_alternative": "string",
      "differences_from_primary": "string"
    }
  ],
  "context": {
    "user_health_conditions": ["string"],
    "dietary_restrictions": ["string"],
    "budget_constraints": "object",
    "cooking_skill_level": "string",
    "regional_preference": "string",
    "current_nutritional_gaps": ["string"]
  },
  "metadata": {
    "algorithm_version": "string",
    "confidence_level": "number (0-1)",
    "generated_by": "enum(automated_ai, human_curated, hybrid)",
    "valid_until": "ISODate"
  }
}
```

---

## Community Contribution Schema

The `contributions` collection tracks community contributions to food data.

```json
{
  "_id": ObjectId,
  "contribution_id": "unique_contribution_id",
  "contributor_id": "string",
  "contribution_type": "enum(food_addition, food_update, nutrition_correction, regional_info_addition, cultural_context_addition)",
  "food_id": "string",
  "food_name": "string",
  "proposed_changes": {
    "added_fields": "object",
    "modified_fields": "object",
    "deleted_fields": ["string"]
  },
  "supporting_evidence": [
    {
      "source_type": "enum(research_paper, medical_journal, government_source, traditional_source, personal_experience)",
      "source_url": "string",
      "reliability_score": "number (0-1)",
      "citation": "string"
    }
  ],
  "status": "enum(pending, under_review, approved, rejected, needs_more_info)",
  "review_history": [
    {
      "reviewer_id": "string",
      "review_timestamp": "ISODate", 
      "action": "enum(approve, reject, request_changes, needs_medical_review)",
      "comments": "string"
    }
  ],
  "metadata": {
    "submitted_at": "ISODate",
    "last_updated_at": "ISODate",
    "upvotes": "number",
    "downvotes": "number",
    "discussion_comments_count": "number",
    "needs_medical_review": "boolean",
    "medical_review_status": "enum(not_required, pending, completed, rejected)"
  }
}
```

---

## Regional Data Schema

The `regional_data` collection stores regional variations of foods and eating habits.

```json
{
  "_id": ObjectId,
  "regional_data_id": "unique_id",
  "region": {
    "state": "string",
    "city": "string",
    "zone": "string (north, south, east, west, central)",
    "cultural_community": "string"
  },
  "food_variations": [
    {
      "food_id": "string",
      "regional_name": "string",
      "preparation_method": "string",
      "ingredient_variations": ["string"],
      "seasonal_availability": {
        "months": ["string (month names)"],
        "season": "string (summer, monsoon, winter, spring, autumn)"
      },
      "cultural_significance": "string",
      "typical_consumption_pattern": "string"
    }
  ],
  "dietary_patterns": {
    "typical_meal_structure": "string",
    "regional_favorites": ["food_id"],
    "common_combinations": [
      {
        "name": "string (e.g., rajma chawal)",
        "foods": ["food_id"],
        "cultural_significance": "string"
      }
    ],
    "festival_foods": [
      {
        "festival": "string",
        "traditional_foods": ["food_id"],
        "preparation_style": "string"
      }
    ]
  },
  "local_markets_info": [
    {
      "market_type": "string (local, wholesale, online)",
      "average_pricing": {
        "food_id": "number (price per kg)"
      },
      "seasonal_availability": "object",
      "geographic_accessibility": "string"
    }
  ],
  "metadata": {
    "last_updated": "ISODate",
    "verified_by": "string",
    "verification_method": "string",
    "community_contributions": "number"
  }
}
```

---

## Medical Validation Schema

The `validations` collection stores medical validation records for health claims.

```json
{
  "_id": ObjectId,
  "validation_id": "unique_validation_id",
  "entity_type": "enum(food, health_claim, recommendation, dietary_rule)",
  "entity_id": "string",
  "claim_type": "enum(beneficial_for, harmful_for, allergen, drug_interaction, nutritional_content)",
  "claim": "string",
  "icmr_source_reference": "string",
  "validation_status": "enum(pending, approved, rejected, outdated)",
  "validation_date": "ISODate",
  "validating_authority": "string (ICMR, AIIMS, etc.)",
  "evidence_summary": "string",
  "evidence_level": "enum(high, moderate, low, consensus, expert_opinion)",
  "confidence_level": "number (0-1)",
  "applicable_population": {
    "age_group": "string",
    "health_condition": "string",
    "geographic_region": "string"
  },
  "contraindications": ["string"],
  "side_effects": ["string"],
  "required_monitoring": ["string"],
  "review_schedule": "string (e.g., annual review required)",
  "metadata": {
    "validated_by": "string",
    "reviewed_by": "string",
    "last_review_date": "ISODate",
    "expires_date": "ISODate (if applicable)"
  }
}
```

---

## API Usage Schema

The `api_usage` collection tracks API usage for rate limiting and analytics.

```json
{
  "_id": ObjectId,
  "usage_id": "unique_usage_id",
  "api_key": "string",
  "user_id": "string",
  "client_ip": "string",
  "request_endpoint": "string",
  "request_method": "string",
  "request_body_size": "number",
  "response_size": "number",
  "response_time_ms": "number",
  "status_code": "number",
  "timestamp": "ISODate",
  "rate_limit_info": {
    "limit_per_minute": "number",
    "remaining_count": "number",
    "reset_time": "ISODate"
  },
  "integration_info": {
    "platform": "string",
    "partner_name": "string",
    "use_case": "string"
  },
  "metadata": {
    "user_agent": "string",
    "location": "string",
    "request_id": "string"
  }
}
```

---

## Indexes and Performance

### MongoDB Indexes

#### Foods Collection
```javascript
// Primary search index
db.foods.createIndex({ "primary_name": "text", "names.local": "text", "names.regional": "text" })

// Category filtering
db.foods.createIndex({ "category.primary": 1 })

// Nutrition-based filtering
db.foods.createIndex({ "nutrition.per_100g.calories": 1 })
db.foods.createIndex({ "nutrition.per_100g.protein_g": 1 })
db.foods.createIndex({ "nutrition.per_100g.carbs_g": 1 })

// Medical consideration filtering
db.foods.createIndex({ "medical_considerations.conditions_to_avoid.condition": 1 })
db.foods.createIndex({ "medical_considerations.beneficial_for.condition": 1 })

// Economic data filtering
db.foods.createIndex({ "economic_data.price_per_kg": 1 })

// Metadata for data quality
db.foods.createIndex({ "metadata.icmr_verified": 1 })
db.foods.createIndex({ "metadata.data_quality_score": -1 })

// Compound indexes for common queries
db.foods.createIndex({
  "category.primary": 1,
  "nutrition.per_100g.calories": 1,
  "medical_considerations.conditions_to_avoid.condition": 1
})
```

#### Users Collection
```javascript
// User lookup
db.users.createIndex({ "user_id": 1 }, { unique: true })

// Location-based queries
db.users.createIndex({ "profile.location.state": 1 })

// Health condition based recommendations
db.users.createIndex({ "health_information.medical_conditions.condition": 1 })
```

#### Recommendations Collection
```javascript
// User's recommendations lookup
db.recommendations.createIndex({ "user_id": 1, "generation_timestamp": -1 })

// Recommendation freshness
db.recommendations.createIndex({ "generation_timestamp": -1 })
```

#### API Usage Collection
```javascript
// Rate limiting
db.api_usage.createIndex({ "api_key": 1, "timestamp": -1 })

// Analytics by date range
db.api_usage.createIndex({ "timestamp": 1 })

// Performance analysis
db.api_usage.createIndex({ "response_time_ms": 1 })
```

### PostgreSQL Indexes

#### User Accounts
```sql
-- Primary key indexes (auto-created)
-- Index for email lookup
CREATE INDEX idx_user_accounts_email ON user_accounts(email);

-- Index for account status checks
CREATE INDEX idx_user_accounts_status ON user_accounts(account_status);
```

#### API Keys
```sql
-- Primary key indexes (auto-created)
-- Index for API key lookups
CREATE INDEX idx_api_keys_key ON api_keys(api_key);

-- Index for rate limiting by user
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
```

---

## Relationships

### Primary Relationships

1. **User → Nutrition Logs**: One-to-Many
   - One user can have many nutrition logs
   - Foreign key: `user_id` in nutrition_logs

2. **User → Recommendations**: One-to-Many
   - One user can have many recommendations
   - Foreign key: `user_id` in recommendations

3. **Food → Contributions**: One-to-Many
   - One food item can have many contributions
   - Foreign key: `food_id` in contributions

4. **User → Contributions**: One-to-Many
   - One user can make many contributions
   - Foreign key: `contributor_id` in contributions

5. **Food → Validations**: One-to-Many
   - One food item can have many validation records
   - Foreign key: `entity_id` in validations where `entity_type` = 'food'

### Cross-Reference Relationships

- Nutrition logs reference food items by `food_id`
- Recommendations reference food items by `item_id`
- Regional data references food items by `food_id`
- Community contributions reference food items by `food_id`

---

## Data Validation Rules

### MongoDB Validation Rules

#### Foods Collection Validation
```javascript
db.createCollection("foods", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["food_id", "primary_name", "category", "nutrition", "metadata"],
      properties: {
        food_id: {
          bsonType: "string",
          minLength: 1,
          description: "Food ID is required and cannot be empty"
        },
        primary_name: {
          bsonType: "string", 
          minLength: 1,
          description: "Primary name is required and cannot be empty"
        },
        category: {
          bsonType: "object",
          required: ["primary"],
          properties: {
            primary: {
              enum: ["grain", "pulse", "vegetable", "fruit", "spice", "herb", "dairy", "meat", "fish", "egg", "oil", "sweet"],
              description: "Primary category must be one of the predefined values"
            }
          }
        },
        nutrition: {
          bsonType: "object",
          required: ["per_100g"],
          properties: {
            per_100g: {
              bsonType: "object",
              required: ["calories", "protein_g", "carbs_g", "fats_g"],
              properties: {
                calories: {
                  bsonType: "number",
                  minimum: 0,
                  description: "Calories must be non-negative"
                },
                protein_g: {
                  bsonType: "number", 
                  minimum: 0,
                  description: "Protein must be non-negative"
                }
              }
            }
          }
        }
      }
    }
  }
})
```

### PostgreSQL Constraints

#### API Keys Table
```sql
-- Ensure API key format
ALTER TABLE api_keys 
ADD CONSTRAINT chk_api_key_format 
CHECK (LENGTH(api_key) >= 32);

-- Ensure unique API keys
ALTER TABLE api_keys 
ADD CONSTRAINT uk_api_key UNIQUE (api_key);
```

#### Health Conditions Table
```sql
-- Ensure approved condition list
ALTER TABLE health_conditions
ADD CONSTRAINT chk_approved_condition
CHECK (condition_name IN (
  'diabetes', 'hypertension', 'heart_disease', 'gout', 'kidney_disease',
  'celiac_disease', 'lactose_intolerance', 'pcos', 'thyroid_disorder',
  'anemia', 'osteoporosis', 'arthritis', 'ibs', 'acidity'
));
```

---

[[Project_IndiByte_Structured]] | [[IndiByte_PRD]] | [[API Documentation]]