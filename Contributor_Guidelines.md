# IndiByte Contributor Guidelines

[Project_IndiByte_Structured](Project_IndiByte_Structured.md) ← Back to Project Overview
[IndiByte_PRD](IndiByte_PRD.md) ← Back to PRD
[API Documentation](API_Documentation.md) ← Back to API Docs
[Database Schema](Database_Schema.md) ← Back to Database Schema

---

## Table of Contents
- [Introduction](#introduction)
- [Code of Conduct](#code-of-conduct)
- [Ways to Contribute](#ways-to-contribute)
- [Getting Started](#getting-started)
- [Contribution Process](#contribution-process)
- [Food Data Contribution Guidelines](#food-data-contribution-guidelines)
- [Documentation Guidelines](#documentation-guidelines)
- [Technical Contribution Guidelines](#technical-contribution-guidelines)
- [Review Process](#review-process)
- [Recognition](#recognition)
- [Resources](#resources)

---

## Introduction

Welcome to the IndiByte contributor community! IndiByte is an open-source platform that standardizes nutrition for India's culinary diversity. Our success depends on contributors like you who help us build the most comprehensive and accurate database of Indian foods.

As a contributor, you'll be part of a mission to make nutritional science accessible, accurate, and culturally appropriate for 1.7 billion people. Whether you're a farmer, doctor, dietitian, chef, researcher, or simply someone passionate about Indian cuisine, your knowledge adds value to the platform.

### Our Values
- **Accuracy**: All contributions must be backed by reliable sources
- **Cultural Sensitivity**: Respecting India's diverse food culture
- **Inclusivity**: Making nutrition accessible across economic tiers
- **Transparency**: Open review and validation process
- **Collaboration**: Working together for the common good

---

## Code of Conduct

### Our Pledge
In the interest of fostering an open and welcoming environment, we as contributors and maintainers pledge to making participation in our project and our community a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards
Examples of behavior that contributes to creating a positive environment include:
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

Examples of unacceptable behavior by participants include:
- The use of sexualized language or imagery and unwelcome sexual attention or advances
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information, such as a physical or electronic address, without explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

### Our Responsibilities
Project maintainers are responsible for clarifying the standards of acceptable behavior and are expected to take appropriate and fair corrective action in response to any instances of unacceptable behavior.

Project maintainers have the right and responsibility to remove, edit, or reject comments, commits, code, wiki edits, issues, and other contributions that are not aligned to this Code of Conduct, or to ban temporarily or permanently any contributor for other behaviors that they deem inappropriate, threatening, offensive, or harmful.

---

## Ways to Contribute

### 1. Food Data Contributions
- Add new Indian foods to the database
- Update nutritional information for existing foods
- Add regional variations and cultural context
- Provide economic data (pricing information)

### 2. Medical Validation
- Verify health claims with ICMR-validated sources
- Flag potentially incorrect medical information
- Provide peer-reviewed research for health benefits

### 3. Technical Contributions
- Improve the API and platform functionality
- Fix bugs and improve performance
- Add new features and integrations
- Enhance documentation

### 4. Documentation
- Write and improve user guides
- Create API documentation
- Update contribution guidelines
- Translate content into regional languages

### 5. Community Building
- Answer questions in forums
- Moderate community discussions
- Organize local meetups
- Spread awareness about the project

---

## Getting Started

### Prerequisites
- Understanding of Indian cuisine and culture
- Access to reliable nutritional data sources
- Commitment to accuracy and verification
- Agreement to the Code of Conduct

### Initial Steps
1. **Join the Community**: Sign up at community.indibyte.org
2. **Read Documentation**: Familiarize yourself with the platform
3. **Choose Contribution Area**: Select what you're most interested in
4. **Start Small**: Begin with minor contributions to understand the process
5. **Ask Questions**: Our community is here to help

### Tools and Setup
- Git version control
- GitHub account for code contributions
- Basic understanding of JSON for data contributions
- Access to nutritional databases or research papers

---

## Contribution Process

### 1. Find Something to Work On
- Check the [Issues](https://github.com/indibyte/issues) page
- Look for "good first issue" or "help wanted" labels
- Join community discussions to identify priorities

### 2. Discuss Your Contribution
- Comment on existing issues or create new ones
- For major changes, start a discussion in our community forum
- Get feedback before starting work to ensure alignment

### 3. Fork, Code, and Submit
- Fork the repository (for code contributions)
- Create a descriptive branch name
- Make your changes following our guidelines
- Submit a pull request with a clear description

### 4. Review and Iterate
- Address feedback from maintainers
- Be responsive during the review process
- Make necessary changes to meet standards

### 5. Celebrate!
- Your contribution is now part of IndiByte
- Thank you for helping improve nutrition for 1.7 billion people

---

## Food Data Contribution Guidelines

### Data Requirements
When contributing food data, ensure you provide:

#### Basic Information
- **Food Name**: Primary name and regional variations
- **Category**: Primary category (grain, pulse, vegetable, etc.)
- **Dietary Type**: Vegetarian, vegan, non-vegetarian, etc.

#### Nutritional Information
- **Per 100g values**:
  - Calories
  - Protein (g)
  - Carbohydrates (g)
  - Fats (g)
  - Fiber (g)
  - Sugar (g)
  - Sodium (mg)
  - Cholesterol (mg)
  - Saturated fat (g)
  - Trans fat (g)

#### Additional Data Points
- **Vitamins**: A, B-complex, C, D, E, K, Folate
- **Minerals**: Calcium, Iron, Magnesium, Phosphorus, Potassium, Zinc, etc.
- **Cultural Context**: Regional prevalence, traditional use, cooking methods
- **Economic Data**: Average price per kg across different regions
- **Medical Considerations**: Benefits, contraindications, allergens

### Data Quality Standards
1. **Source Verification**: All data must come from reliable sources
2. **Multiple Sources**: Cross-reference information when possible
3. **ICMR Alignment**: Prefer ICMR-validated data when available
4. **Units Consistency**: Use standard units (g, mg, mcg, IU)
5. **Regional Accuracy**: Account for regional variations in preparation

### Sourcing Guidelines
- **Government Sources**: ICMR, Ministry of Agriculture, FSSAI
- **Research Papers**: Peer-reviewed journals
- **Established Databases**: USDA FoodData Central (for comparison)
- **Expert Knowledge**: Dietitians, nutritionists, medical professionals
- **Local Knowledge**: Regional experts, farmers, food historians

### Example Contribution Format
```json
{
  "primary_name": "Toor Dal",
  "names": {
    "local": ["Toor Dal", "Arhar Dal", "Red Gram"],
    "regional": {
      "hindi": "अरहर दाल",
      "bengali": "মসুর ডাল",
      "tamil": "துவரம் பருப்பு",
      "telugu": "పెసరలు",
      "marathi": "तूर डाळ"
    }
  },
  "category": {
    "primary": "pulse",
    "secondary": ["legume", "lentil"],
    "dietary_type": ["vegetarian", "vegan"]
  },
  "nutrition": {
    "per_100g": {
      "calories": 343,
      "protein_g": 22.6,
      "carbs_g": 62.1,
      "fats_g": 1.2,
      "fiber_g": 4.4,
      "sugar_g": 0.7
    },
    "vitamins": {
      "folate_mcg": 250,
      "thiamin_mg": 0.56,
      "niacin_mg": 1.5
    },
    "minerals": {
      "phosphorus_mg": 278,
      "potassium_mg": 965,
      "iron_mg": 3.2,
      "magnesium_mg": 76
    }
  },
  "cultural_context": {
    "regional_prevalence": "Staple across India, especially South and West",
    "traditional_use": "Daily meal component, religious significance",
    "cooking_methods": ["Boiled with turmeric", "Added to sambar", "In dal fry"]
  },
  "economic_data": {
    "price_per_kg": 85,
    "price_currency": "INR",
    "affordability_index": 9
  },
  "medical_considerations": {
    "beneficial_for": [
      {
        "condition": "diabetes",
        "validation_source": "ICMR-DIABETES-2023-001",
        "notes": "High fiber content helps regulate blood sugar"
      }
    ],
    "conditions_to_avoid": [
      {
        "condition": "kidney_stones",
        "severity": "moderate",
        "notes": "Oxalate content may contribute to stone formation"
      }
    ],
    "allergens": []
  },
  "metadata": {
    "source": "ICMR National Institute of Nutrition",
    "source_date": "2023-08-15",
    "contributed_by": "user_id",
    "verified_by": "medical_reviewer_id"
  }
}
```

---

## Documentation Guidelines

### Writing Style
- Use clear, concise language
- Write for a diverse audience (technical and non-technical)
- Use active voice where possible
- Be specific rather than vague

### Technical Documentation
- Include code examples in multiple languages when applicable
- Provide use cases and practical examples
- Explain the "why" behind the "what"
- Keep examples updated with the latest API versions

### Formatting Standards
- Use proper heading hierarchy (#, ##, ###)
- Format code blocks with appropriate language tags
- Use bullet points for lists
- Include hyperlinks to related documentation

---

## Technical Contribution Guidelines

### Code Standards
- Follow the established code style of the project
- Write clear, descriptive commit messages
- Include tests for new functionality
- Document your code appropriately

### Pull Request Requirements
- One logical change per pull request
- Include tests for new functionality
- Update documentation if necessary
- All checks must pass before review
- Link to relevant issues if applicable

### Branch Naming Convention
- Feature: `feature/descriptive-name`
- Bug Fix: `fix/descriptive-name`
- Documentation: `docs/descriptive-name`

---

## Review Process

### Initial Review
- Automated checks (formatting, basic validation)
- Assignment to appropriate reviewer
- Initial feedback within 48 hours

### Technical Review
- Code quality and functionality
- Security and performance considerations
- Integration with existing systems

### Medical Review
- For food data contributions
- Verification of nutritional and health claims
- ICMR source validation
- Medical accuracy confirmation

### Final Approval
- Maintainer approval
- Integration into platform
- Contributor recognition

### Timeline Expectations
- **Small contributions**: 1-3 days
- **Medium contributions**: 3-7 days
- **Large contributions**: 1-2 weeks
- **Medical data**: Up to 2 weeks (due to validation requirements)

---

## Recognition

### How We Acknowledge Contributors
- Public recognition in release notes
- Contributor badges in community profile
- Annual contributor appreciation events
- Co-authorship opportunities on research papers
- Feature naming rights for significant contributions

### Levels of Recognition
- **Community Contributor**: Regular, valuable contributions
- **Distinguished Contributor**: Exceptional contributions that significantly impact the project
- **Community Leader**: Ongoing leadership in community management and growth

---

## Resources

### Getting Help
- **Community Forum**: community.indibyte.org
- **Documentation**: docs.indibyte.org
- **Issues**: github.com/indibyte/issues
- **Direct Contact**: contributors@indibyte.org

### Learning Materials
- **Platform Overview**: Video tutorials and guides
- **API Documentation**: Complete reference
- **Data Standards**: Nutritional data requirements
- **Regional Guides**: Information about different regional cuisines

### Tools and References
- ICMR publications
- FSSAI guidelines
- USDA FoodData Central
- Indian Council of Agricultural Research resources

---

## Questions?

If you have any questions about contributing to IndiByte:
1. Check the [FAQ](FAQ.md) first
2. Search in the [Community Forum](https://community.indibyte.org)
3. Create a new post in the forum
4. Contact the community team at contributors@indibyte.org

---

*Thank you for contributing to IndiByte! Together, we're building a platform that makes culturally appropriate, accurate nutrition accessible to 1.7 billion people.*

[Project_IndiByte_Structured](Project_IndiByte_Structured.md) | [IndiByte_PRD](IndiByte_PRD.md) | [API Documentation](API_Documentation.md) | [Database Schema](Database_Schema.md)