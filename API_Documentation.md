# IndiByte API Documentation

[Project_IndiByte_Structured](Project_IndiByte_Structured.md) ← Back to Project Overview
[IndiByte_PRD](IndiByte_PRD.md) ← Back to PRD

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Rate Limiting](#rate-limiting)
- [Endpoints](#endpoints)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [SDKs & Libraries](#sdks--libraries)
- [Examples](#examples)

---

## Overview

The IndiByte API provides programmatic access to India's comprehensive database of food nutrition, cultural context, and dietary recommendations. Our API is designed to be integration-friendly for health platforms, food delivery apps, dietitians, and AI systems.

### API Version

- Current Version: v1
- Base Path: `/api/v1`

### Core Principles

- **Zero Cost for Public Health**: Free access for government health initiatives and non-profits
- **Machine-Readable**: Optimized for programmatic consumption
- **Real-time Data**: Up-to-date information on Indian foods and nutrition
- **Cultural Sensitivity**: Indian-first approach to food data

---

## Authentication

The IndiByte API uses API Key authentication:

```
Authorization: Bearer YOUR_API_KEY
```

### Getting an API Key

- For commercial use: Register at api.indibyte.org/register
- For public health use: Automatically approved with verification
- For development: Request a sandbox key (1000 requests/day)

---

## Base URL

Production: `https://api.indibyt.org/v1`

Sandbox: `https://sandbox.api.indibyte.org/v1`

---

## Rate Limiting

| **Tier** | **Requests/Minute** | **Requests/Day** | **Use Case** |
|----------|-------------------|------------------|--------------|
| Public Health | 1000 | Unlimited | Government initiatives |
| Developer | 100 | 1000 | Testing/integration |
| Commercial | 1000 | 100,000 | Production applications |

Rate limit headers are returned in all responses:

- `X-RateLimit-Limit`: Request limit for the time window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the current window resets

---

## Endpoints

### Food Data Endpoints

#### GET /foods

Search for Indian foods in the database.

**Parameters**:

- `q` (string, optional): Search query (food name, ingredient)
- `category` (string, optional): Food category filter (e.g., "vegetable", "pulse", "fish", "spice")
- `limit` (integer, optional): Number of results (1-50, default: 10)
- `offset` (integer, optional): Offset for pagination (default: 0)
- `min_protein` (number, optional): Minimum protein content (g per 100g)
- `max_calories` (number, optional): Maximum calories (per 100g)
- `medical_condition` (string, optional): Condition-specific recommendations (e.g., "diabetes", "gout")

**Example Request**:

```
GET /api/v1/foods?q=roti&category=grain&limit=5
Authorization: Bearer YOUR_API_KEY
```

**Response**:

```json
{
  "data": [
    {
      "id": "roti-wholewheat",
      "name": "Whole Wheat Roti",
      "aliases": ["Chapati", "phulka", "rotla"],
      "category": "grain",
      "nutrition": {
        "calories": 104,
        "protein": 3.2,
        "carbs": 20.8,
        "fats": 0.7,
        "fiber": 2.2,
        "vitamins": {
          "thiamin": 0.133,
          "niacin": 2.17,
          "folate": 18
        },
        "minerals": {
          "iron": 1.59,
          "magnesium": 23,
          "phosphorus": 88,
          "potassium": 81
        }
      },
      "cultural_context": "Staple bread across North India, made from whole wheat flour. Essential part of most Indian meals.",
      "economic_tier": {
        "price_per_kg": 35,
        "currency": "INR"
      },
      "medical_considerations": {
        "conditions_to_avoid": ["celiac_disease"],
        "beneficial_for": ["diabetes", "digestive_health"],
        "allergens": ["wheat", "gluten"]
      },
      "preparation_methods": [
        "Roll dough into thin circles, cook on hot griddle, puff with heat"
      ],
      "regional_variations": [
        "Punjab: Thicker roti with ghee",
        "Gujarat: Thinner, with oil on both sides",
        "Rajasthan: Bajra or jowar roti common"
      ],
      "tags": ["staple", "fiber_rich", "diabetic_friendly", "gluten_containing"]
    }
  ],
  "pagination": {
    "total": 1,
    "limit": 5,
    "offset": 0,
    "has_more": false
  }
}
```

#### GET /foods/{id}

Get detailed information for a specific food item.

**Path Parameters**:

- `id` (string): Unique identifier for the food item

**Example Request**:

```
GET /api/v1/foods/rohu-fish
Authorization: Bearer YOUR_API_KEY
```

**Response**:

```json
{
  "data": {
    "id": "rohu-fish",
    "name": "Rohu Fish",
    "aliases": ["Rui", "Carpa rohita", "Thai Thailla"],
    "category": "fish",
    "nutrition": {
      "calories": 120,
      "protein": 22.0,
      "carbs": 0,
      "fats": 3.5,
      "omega_3": 0.8,
      "vitamins": {
        "b12": 2.5,
        "d": 5.0,
        "niacin": 4.5
      },
      "minerals": {
        "phosphorus": 210,
        "potassium": 340,
        "selenium": 25.5
      }
    },
    "cultural_context": "Common in coastal South India and Bengal. High omega-3 content but avoid with gout (high purines).",
    "economic_tier": {
      "price_per_kg": 120,
      "currency": "INR"
    },
    "medical_considerations": {
      "conditions_to_avoid": ["gout", "fish_allergy"],
      "beneficial_for": ["cardiovascular_health", "brain_function"],
      "allergens": ["fish"]
    },
    "preparation_methods": [
      "Mustard gravy preparation (Bengali style)",
      "Red chili paste with tamarind (South Indian)",
      "Fried with turmeric and salt"
    ],
    "regional_variations": [
      "Bengal: Jhol with mustard and poppy seeds",
      "South: In sambar and rasam",
      "North: In fish curry with yogurt"
    ],
    "tags": ["omega_3_rich", "high_protein", "gout_caution", "indian_staple"]
  }
}
```

#### POST /foods/search

Advanced search with multiple filters.

**Request Body**:

```json
{
  "query": "dal",
  "filters": {
    "categories": ["pulse", "legume"],
    "max_calories": 300,
    "min_protein": 20,
    "medical_condition": "diabetes",
    "dietary_restrictions": ["vegan", "gluten_free"],
    "max_price_per_kg": 100,
    "regional_preference": "south_indian"
  },
  "sort_by": "protein",
  "sort_order": "desc",
  "limit": 10
}
```

**Response**:

```json
{
  "data": [
    {
      "id": "toor-dal",
      "name": "Toor Dal (Pigeon Pea)",
      "relevance_score": 0.95,
      "nutrition": {
        "calories": 343,
        "protein": 22.6,
        "carbs": 62.1,
        "fats": 1.2
      },
      "cultural_context": "Staple of South Indian cuisine, also popular in Gujarat and Maharashtra.",
      "economic_tier": {
        "price_per_kg": 85
      },
      "medical_considerations": {
        "beneficial_for": ["diabetes", "heart_health"],
        "conditions_to_avoid": ["kidney_stones"],
        "allergens": []
      }
    }
  ],
  "filters_applied": {
    "categories": ["pulse", "legume"],
    "max_calories": 300,
    "min_protein": 20,
    "medical_condition": "diabetes"
  },
  "pagination": {
    "total": 1,
    "limit": 10,
    "offset": 0,
    "has_more": false
  }
}
```

### Personalization Endpoints

#### POST /recommendations/personalized

Generate personalized food recommendations based on user profile.

**Request Body**:

```json
{
  "user_profile": {
    "age": 35,
    "gender": "female",
    "weight_kg": 68,
    "height_cm": 165,
    "medical_conditions": ["diabetes", "hypertension"],
    "dietary_preferences": ["vegetarian"],
    "budget_constraint": {
      "max_price_per_meal": 120,
      "currency": "INR"
    },
    "regional_preference": "bengali",
    "cooking_skills": "intermediate",
    "allergies": ["cashews"]
  },
  "meal_type": "lunch",
  "restrictions": ["low_salt", "low_gi"],
  "goals": ["weight_management", "blood_sugar_control"]
}
```

**Response**:

```json
{
  "recommendations": [
    {
      "id": "bengali-dal-vegetable",
      "name": "Bengali Dal with Mixed Vegetables",
      "meal_component": "main_dish",
      "ingredients": ["toor_dal", "bottle_gourd", "radish", "spinach"],
      "nutrition_per_serving": {
        "calories": 280,
        "protein": 15.2,
        "carbs": 35.8,
        "fats": 8.4
      },
      "cost_estimate": {
        "total_price": 45,
        "currency": "INR"
      },
      "cultural_alignment": 0.95,
      "health_score": 0.88,
      "preparation_time_minutes": 45,
      "instructions_url": "/recipes/bengali-dal-vegetable",
      "meal_plan_suggestion": {
        "pair_with": ["red_rice", "bengali_roti"],
        "avoid_with": ["fried_snacks", "sugary_desserts"]
      },
      "medical_considerations": {
        "benefits": ["low_glycemic", "high_fiber", "cardiovascular_support"],
        "cautions": ["moderate_portion_size"]
      }
    }
  ],
  "alternative_options": [
    {
      "id": "bengali-fish-curry-alternative",
      "name": "Rohu Fish Curry (if non-vegetarian allowed)",
      "health_score": 0.92
    }
  ],
  "nutritional_summary": {
    "total_calories": 420,
    "total_protein": 22.5,
    "total_carbs": 52.3,
    "total_fats": 12.1,
    "fiber": 8.7,
    "meets_daily_requirements": {
      "protein": 0.45,
      "fiber": 0.35,
      "vitamin_a": 0.60
    }
  }
}
```

#### GET /recommendations/popular

Get trending or popular food recommendations based on region or dietary needs.

**Parameters**:

- `region` (string, optional): Regional preference (e.g., "south_indian", "bengali", "punjabi")
- `diet_type` (string, optional): Diet type (e.g., "diabetic", "weight_loss", "heart_healthy")
- `season` (string, optional): Seasonal preference (e.g., "summer", "winter")
- `population_group` (string, optional): Target group (e.g., "pregnant_women", "elderly", "children")

**Example Request**:

```
GET /api/v1/recommendations/popular?region=bengali&diet_type=diabetic&season=winter
Authorization: Bearer YOUR_API_KEY
```

### Recipe Endpoints

#### GET /recipes/{id}

Get detailed recipe instructions.

**Response**:

```json
{
  "data": {
    "id": "bengali-dal-vegetable",
    "name": "Traditional Bengali Dal with Mixed Vegetables",
    "preparation_time": 45,
    "cooking_time": 30,
    "total_time": 75,
    "servings": 4,
    "cuisine_style": "bengali",
    "difficulty": "intermediate",
    "ingredients": [
      {
        "name": "Toor Dal",
        "quantity": "1 cup",
        "weight_g": 200
      },
      {
        "name": "Bottle Gourd",
        "quantity": "200g",
        "weight_g": 200
      }
    ],
    "instructions": [
      {
        "step": 1,
        "description": "Wash and soak toor dal for 30 minutes",
        "time_estimate": 30
      }
    ],
    "nutrition_per_serving": {
      "calories": 280,
      "protein": 15.2,
      "carbs": 35.8,
      "fats": 8.4
    },
    "dietary_info": {
      "vegetarian": true,
      "vegan": true,
      "gluten_free": true,
      "diabetic_friendly": true
    },
    "cooking_tips": [
      "Add turmeric while cooking dal for better digestion",
      "Use mustard oil for authentic Bengali flavor"
    ]
  }
}
```

### Integration Endpoints

#### POST /integration/validate-food

Validate if a food item exists in our database for integration purposes.

**Request Body**:

```json
{
  "food_name": "Chole Bhature",
  "ingredients": ["chickpeas", "flour", "onions", "tomatoes"],
  "brand_name": "Delhi Famous",
  "location_served": "Delhi"
}
```

**Response**:

```json
{
  "matches": [
    {
      "id": "chole-bhature-standard",
      "name": "Chole Bhature (Standard)",
      "confidence": 0.85,
      "nutrition_comparison": {
        "calories_diff": 15,
        "protein_diff": 2,
        "disclaimer": "Approximate match based on standard recipe"
      }
    }
  ],
  "recommendations": [
    {
      "action": "use_normalized_data",
      "message": "Use standardized nutrition data for chole bhature",
      "normalized_nutrition": {
        "calories": 420,
        "protein": 12.5,
        "carbs": 58.2,
        "fats": 15.8
      }
    }
  ]
}
```

---

## Response Format

All API responses follow this standard format:

```json
{
  "status": "success",
  "data": { ... }, // or array of objects
  "message": "Optional message for success",
  "timestamp": "2025-11-11T10:30:00Z",
  "request_id": "unique-request-id"
}
```

For error responses:

```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional details about the error"
  },
  "timestamp": "2025-11-11T10:30:00Z",
  "request_id": "unique-request-id"
}
```

---

## Error Handling

### HTTP Status Codes

| **Code** | **Meaning** | **Description** |
|----------|-------------|-----------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid API key |
| 403 | Forbidden | API key doesn't have required permissions |
| 404 | Not Found | Requested resource doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error, please try again |

### Error Codes

| **Code** | **Description** |
|----------|-----------------|
| INVALID_API_KEY | Provided API key is invalid or expired |
| RATE_LIMIT_EXCEEDED | Request rate limit has been exceeded |
| RESOURCE_NOT_FOUND | Requested food/dish doesn't exist in database |
| INVALID_PARAMETERS | Required parameters are missing or invalid |
| SERVER_ERROR | Internal server error occurred |

---

## SDKs & Libraries

### Node.js

```bash
npm install indibyte-api
```

### Python

```bash
pip install indibyte-api
```

### Java

```xml
<dependency>
    <groupId>org.indibyte</groupId>
    <artifactId>api-client</artifactId>
    <version>1.0.0</version>
</dependency>
```

---

## Examples

### JavaScript (Node.js)

```javascript
const { IndiByteClient } = require('indibyte-api');

const client = new IndiByteClient('YOUR_API_KEY');

// Search for foods
async function searchFoods() {
  try {
    const response = await client.foods.search({
      q: 'dal',
      max_calories: 300,
      min_protein: 20
    });
    
    console.log('Found foods:', response.data);
  } catch (error) {
    console.error('Error:', error.message);
  }
}

// Get personalized recommendations
async function getRecommendations() {
  const userProfile = {
    medical_conditions: ['diabetes'],
    dietary_preferences: ['vegetarian'],
    budget_constraint: { max_price_per_meal: 120 }
  };
  
  const recommendations = await client.recommendations.personalized({
    user_profile: userProfile,
    meal_type: 'lunch'
  });
  
  console.log('Recommendations:', recommendations.data);
}
```

### Python

```python
from indibyte_api import IndiByteClient

client = IndiByteClient('YOUR_API_KEY')

# Search for diabetic-friendly foods
diabetic_foods = client.foods.search(
    q='roti',
    medical_condition='diabetes'
)

# Get nutrition info for Rohu fish
rohu_info = client.foods.get('rohu-fish')
print(f"Rohu has {rohu_info['nutrition']['protein']}g protein per 100g")

# Generate meal recommendations
recommendations = client.recommendations.personalized(
    user_profile={
        'medical_conditions': ['diabetes'],
        'dietary_preferences': ['vegetarian']
    },
    meal_type='dinner'
)
```

---

## Webhook Endpoints

For real-time updates, register webhook endpoints:

#### POST /webhooks/register

```json
{
  "event_type": "food_database_update",
  "callback_url": "https://your-app.com/webhook/indibyte-updates",
  "api_key_verification": true
}
```

Supported events:

- `food_database_update`: When new foods are added or existing ones updated
- `nutritional_guidance_update`: When medical recommendations are updated
- `regional_preference_update`: When regional food preferences change

---

## Changelog

### v1.0.0 (Current)

- Initial public release
- Food search with comprehensive nutrition data
- Personalized recommendation engine
- Regional and cultural food information
- Medical condition-based filtering

---

## Support

For API support:

- Email: <api-support@indibyte.org>
- Documentation: <https://docs.indibyte.org>
- Community: <https://community.indibyte.org>

---

[Project_IndiByte_Structured](Project_IndiByte_Structured.md) | [IndiByte_PRD](IndiByte_PRD.md)
