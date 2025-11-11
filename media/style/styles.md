# IndiByte Animation Style Guide

This document defines how to use the CSS elements from `indibyte-animation-theme.css` to create consistent animations using traditional Indian art styles (particularly Warli) for the IndiByte project.

## Color System

### Primary Palette

- `--primary-dark-bg`: Use as the main background color for all scenes, featuring traditional Warli off-white/creamy background
- `--primary-text`: Use black text for high contrast against traditional backgrounds
- `--primary-accent`: For important UI elements using traditional Warli earthy brown
- `--secondary-accent`: For highlights using deep red common in traditional Indian art
- `--tertiary-accent`: For positive outcomes using deep green from Indian art traditions

### Traditional Indian Art Colors

- `--warli-ochre`: Traditional ochre color used in Warli art
- `--warli-orange`: Traditional orange-brown used in Warli art
- `--warli-cream`: Traditional background color that represents Warli on walls
- `--indian-art-black`: For outlines in traditional Indian art style
- `--indian-art-white`: For highlights in traditional Indian art
- `--indian-art-yellow`: Bright yellow common in Indian folk art
- `--indian-art-blue`: Bright blue used in some Indian art forms

### India-Specific Colors

- `--india-saffron`: For elements representing Indian culture and identity
- `--india-green`: For growth, health, and positive outcomes related to Indian foods
- `--india-peacock`: For elements representing traditional Indian knowledge and culture

### Food-Related Colors

- `--rohu-fish`: For Rohu fish and other Indian fish varieties
- `--toor-dal`: For Toor Dal and other Indian lentils
- `--roti-brown`: For Indian breads and grains
- `--vegetable-green`: For vegetables and plant-based foods
- `--spice-red`: For spices and flavor elements

## CSS Class Application

### Geometric Shapes (Warli Style)

For basic geometric shapes in traditional Indian art style, apply the Warli-inspired classes:

- Use `kurzgesagt-shape` for primary elements (now using Warli colors)
- Use `kurzgesagt-shape-secondary` for supporting elements
- Use `kurzgesagt-shape-tertiary` for accent elements
- Use `kurzgesagt-shape-warli` for elements specifically in Warli style
- Use `kurzgesagt-shape-india` for India-specific elements

### Text Elements

- Apply `animation-title` class for main titles in scenes
- Use `animation-subtitle` for section headers
- Apply `animation-body` for body text and narrated descriptions

### Data Visualization

- Use `chart-bar-positive` for positive statistics (e.g., increased meal orders)
- Use `chart-bar-negative` for concerning statistics (e.g., ignored advice)
- Use `chart-bar-neutral` for baseline or neutral data
- Use `chart-highlight` for key metrics to emphasize

### Character Design

- Apply `character-skin-light`, `character-skin-medium`, or `character-skin-dark` for diverse representation
- Use these classes consistently for all human character elements
- Characters should be designed using simple geometric shapes (circles, triangles, lines) as in Warli art

### Technology Elements

- Use `tech-connection` for data flow lines and network connections
- Apply `tech-ai` for AI-related elements and visualizations
- Use `tech-validation` for quality check and validation elements
- Apply `tech-community` for community collaboration elements

## Scene-Specific Applications with Traditional Indian Art Style

### Scene 1: Opening Hook

- Background: `--primary-dark-bg` (traditional Warli creamy background)
- Cities: Represent using simple geometric Warli-style shapes
- Text: `animation-title` for main text with `--primary-text` color
- Population counter: `statistic-highlight` for the 1.7 billion figure

### Scene 2: Setup Problem

- Doctor and patient characters: Represent as simple geometric Warli-style figures (triangles for bodies, circles for heads)
- Food comparison: Use geometric shapes with `--rohu-fish` and other food colors
- Global restaurant chain: Represent with simple Warli-style geometric forms

### Scene 3: Scale

- Earth visualization: `background-gradient-warli` using traditional colors
- Population counter: Simple geometric figures to represent the 1.7 billion
- Statistics: `chart-bar-negative` for 89% ignoring advice, visualized in traditional art style
- Transition elements: Use Warli-style geometric transitions

### Scene 4: Economic Reality

- Food items: Represent as geometric shapes using appropriate food color variables
- Price tags: Use `--secondary-accent` for emphasis
- Wallets/budget: Visualize with simple Warli-style geometric forms

### Scene 5: Technical Solution

- Infrastructure elements: Use geometric network connections in traditional colors
- IndiByte logo: Incorporate elements inspired by Warli style with `--india-saffron` accents
- Components: Represent as simple geometric forms in Warli style

### Scene 6: Database

- Library metaphor: Represent books as simple geometric rectangles in Warli style
- Food items: Use geometric representations with specific food color variables
- ICMR elements: Use `--india-peacock` to represent the authority

### Scene 7: AI Engine

- Processing elements: Visualize as geometric patterns in traditional colors
- Inputs/outputs: Use simple geometric shapes in `--secondary-accent` and `--tertiary-accent`
- Algorithm pathways: Represent as simple line connections in Warli-inspired style

### Scene 8: API Infrastructure

- Connection network: Use simple lines and geometric nodes in traditional art style
- Platform icons: Use geometric forms with appropriate accent colors
- Data packets: Simple geometric shapes in traditional colors

### Scene 9: Pilot Success

- Statistics: Use geometric charts in `--chart-bar-positive` colors
- Zomato interface: Adapt elements to use geometric, Warli-inspired design
- Success indicators: Use geometric positive symbols in traditional colors

### Scene 10: Community Validation

- Contributors: Simple geometric Warli-style figures representing different people
- Collaboration elements: Use traditional geometric community symbols
- Validation checks: Simple geometric validation symbols

### Scene 11: Scale of Impact

- Growth visualization: Use geometric growth patterns in traditional colors
- 10M+ target: Geometric representation with `statistic-highlight` class
- Timeline: Simple geometric progression elements

### Scene 12: Vision

- Bridge metaphor: Represent as geometric construction in Warli style
- 1.7 billion visualization: Use large number of simple geometric figures
- IndiByte logo: Incorporate Warli-style elements with `--india-saffron` accents
- Conclusion elements: Use geometric celebration symbols in traditional colors

## Animation Classes

### Movement Animations

- Use `fade-in` for elements that should appear gradually
- Apply `slide-in-left` for elements entering from the left
- Use `slide-in-right` for elements entering from the right

### Interactive Elements

- Add `interactive-highlight` for elements that need emphasis
- Include `interactive-hover` for elements that respond to interaction

## Traditional Indian Art Style Principles

### Warli Art Implementation

1. Use simple geometric shapes: circles for heads, triangles for bodies, lines for limbs
2. Focus on human activities and daily life
3. Use minimal colors - primarily earth tones with occasional bright accents
4. Create narrative sequences that tell a story
5. Use rhythmic patterns and repetitive elements

### Design Guidelines

1. Simplicity: Use only essential elements, following Warli's minimalist approach
2. Narrative Focus: Ensure visual elements support the story being told
3. Cultural Authenticity: Respect traditional Indian art forms while adapting for animation
4. Visual Consistency: Maintain the geometric, simplified style throughout
5. Color Restraint: Use traditional Warli colors primarily, with Indian flag colors for emphasis

## Best Practices

1. Consistency: Always use CSS variables instead of hardcoded colors to maintain visual consistency
2. Accessibility: Ensure sufficient contrast between text and background colors
3. Cultural Sensitivity: Honor traditional Indian art forms while adapting them for modern animation
4. Warli Aesthetic: Use simple geometric shapes and earth tones that match the traditional style
5. Readability: Use `--primary-text` for all text elements to maintain consistency and readability
6. Simplicity: Embrace the minimalist approach of traditional Indian art forms

## Implementation in Animation Tools

### For Blender

- Use the CSS color variables as references for material colors
- Create material palettes based on traditional Indian art colors
- Apply geometric, simplified modeling approach inspired by Warli art
- Focus on clean, simple shapes rather than detailed forms

### For Inkscape

- Import traditional Indian art colors to the palette based on the CSS variables
- Use geometric shapes tools to create Warli-style elements
- Create reusable symbols for common Warli-style elements (people, animals, buildings)
- Use simple line weights and minimal detail

### For Friction (After Effects alternative)

- Create a color palette composition with all traditional art theme colors
- Use expressions to reference the theme colors in effects
- Apply geometric, simplified animation principles
- Focus on shape-based animations rather than complex 3D effects
