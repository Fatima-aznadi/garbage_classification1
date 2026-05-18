import streamlit as st
import streamlit.components.v1 as components
import tensorflow as tf
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import cv2
import time
import os
import json
from datetime import datetime
import plotly.graph_objects as go
import pandas as pd
import urllib.request
import urllib.parse
import math

st.set_page_config(
    page_title="EcoScan AI ♻️",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

CLASS_NAMES = ['cardboard', 'glass', 'metal', 'paper', 'plastic', 'trash']

INFOS = {
    'cardboard': {
        "emoji": "📦", "couleur": "#F59E0B",
        "poubelle": "🟡 Poubelle jaune", "poubelle_color": "#F59E0B",
        "conseil": "Aplatir le carton avant de le recycler.",
        "fun_fact": "Recycler 1 tonne de carton sauve 17 arbres et 4000 kWh d'énergie.",
        "impact": "Recycler le carton sauve des arbres.",
        "exemples": "Boîtes, emballages, rouleaux",
        "recyclable": True, "co2_kg": 0.9, "recyclage_rate": 82, "decomposition": "2-5 mois",
    },
    'glass': {
        "emoji": "🍾", "couleur": "#10B981",
        "poubelle": "🟢 Borne à verre", "poubelle_color": "#10B981",
        "conseil": "Déposer dans une borne à verre.",
        "fun_fact": "Le verre peut être recyclé à l'infini sans perte de qualité !",
        "impact": "Le verre est recyclable à l'infini.",
        "exemples": "Bouteilles, bocaux, flacons",
        "recyclable": True, "co2_kg": 0.31, "recyclage_rate": 90, "decomposition": "4000 ans",
    },
    'metal': {
        "emoji": "🥫", "couleur": "#6366F1",
        "poubelle": "🟡 Poubelle jaune", "poubelle_color": "#F59E0B",
        "conseil": "Rincer avant de recycler.",
        "fun_fact": "Recycler une canette économise assez d'énergie pour faire tourner une TV 3h.",
        "impact": "Recycler l'aluminium économise beaucoup d'énergie.",
        "exemples": "Canettes, boîtes de conserve",
        "recyclable": True, "co2_kg": 1.7, "recyclage_rate": 75, "decomposition": "200-500 ans",
    },
    'paper': {
        "emoji": "📄", "couleur": "#FBBF24",
        "poubelle": "🟡 Poubelle jaune", "poubelle_color": "#F59E0B",
        "conseil": "Papier propre et sec uniquement.",
        "fun_fact": "Recycler 1 tonne de papier économise 26 000 litres d'eau.",
        "impact": "Recycler le papier économise l'eau.",
        "exemples": "Feuilles, journaux, magazines",
        "recyclable": True, "co2_kg": 0.7, "recyclage_rate": 65, "decomposition": "2-5 semaines",
    },
    'plastic': {
        "emoji": "♻️", "couleur": "#3B82F6",
        "poubelle": "🟡 Poubelle jaune", "poubelle_color": "#F59E0B",
        "conseil": "Rincer les bouteilles avant recyclage.",
        "fun_fact": "Chaque minute, 1 million de bouteilles plastiques sont achetées dans le monde.",
        "impact": "Recycler le plastique économise de l'énergie.",
        "exemples": "Bouteilles, sachets, flacons",
        "recyclable": True, "co2_kg": 2.5, "recyclage_rate": 30, "decomposition": "450-1000 ans",
    },
    'trash': {
        "emoji": "🗑️", "couleur": "#6B7280",
        "poubelle": "⚫ Poubelle noire", "poubelle_color": "#374151",
        "conseil": "Déchet non recyclable.",
        "fun_fact": "Réduire ses déchets à la source est 10x plus efficace que le recyclage.",
        "impact": "Réduire les déchets protège l'environnement.",
        "exemples": "Restes alimentaires, mouchoirs",
        "recyclable": False, "co2_kg": 0.0, "recyclage_rate": 0, "decomposition": "Variable",
    },
}

RECYCLING_FILTERS = {
    'cardboard': ['recycling:cardboard', 'recycling:paper', 'recycling:paper_packaging'],
    'glass':     ['recycling:glass', 'recycling:glass_bottles'],
    'metal':     ['recycling:metal', 'recycling:aluminium', 'recycling:steel', 'recycling:can'],
    'paper':     ['recycling:paper', 'recycling:cardboard', 'recycling:magazines'],
    'plastic':   ['recycling:plastic', 'recycling:plastic_bottles', 'recycling:plastic_packaging'],
    'trash':     [],
}
TAG_LABELS = {
    'glass': 'Verre', 'glass_bottles': 'Bouteilles verre',
    'paper': 'Papier', 'cardboard': 'Carton', 'paper_packaging': 'Emballages papier',
    'plastic': 'Plastique', 'plastic_bottles': 'Bouteilles plastique',
    'plastic_packaging': 'Emballages plastique',
    'metal': 'Métal', 'aluminium': 'Aluminium', 'steel': 'Acier', 'can': 'Canettes',
    'clothes': 'Vêtements', 'shoes': 'Chaussures',
    'electrical_appliances': 'Électroménager', 'small_electrical_appliances': 'Petit électroménager',
    'batteries': 'Piles', 'green_waste': 'Déchets verts',
    'cooking_oil': 'Huile cuisine', 'engine_oil': 'Huile moteur',
    'timber': 'Bois', 'tyres': 'Pneus', 'scrap_metal': 'Ferraille',
    'organic': 'Organique', 'waste': 'Déchets',
    'cans': 'Canettes', 'cartons': 'Cartons',
    'beverage_cartons': 'Cartons boisson',
}
TYPE_LABELS = {
    'container': '🟢 Conteneur', 'centre': '🏭 Centre de recyclage',
    'overground': '🔵 Point surélevé', 'underground': '⚫ Point enterré',
}
COUNTRIES = {
    "fr": "🇫🇷 France", "be": "🇧🇪 Belgique", "ch": "🇨🇭 Suisse",
    "lu": "🇱🇺 Luxembourg", "de": "🇩🇪 Allemagne", "es": "🇪🇸 Espagne",
    "it": "🇮🇹 Italie", "gb": "🇬🇧 Royaume-Uni", "ca": "🇨🇦 Canada",
    "ma": "🇲🇦 Maroc", "tn": "🇹🇳 Tunisie", "sn": "🇸🇳 Sénégal",
    "ci": "🇨🇮 Côte d'Ivoire",
}

CHATBOT_KB = [
    {
        "id": "piles",
        "kw_fr": ["pile", "piles", "batterie", "batteries", "accumulateur"],
        "kw_darija": ["بياريات", "بياريه", "لباري", "بطاريات", "بطاريه", "البطاريات"],
        "icon": "🔋",
        "title": "Piles et batteries",
        "answer": (
            "Les piles et batteries **ne vont JAMAIS** dans une poubelle normale !\n\n"
            "📋 **Où les déposer :**\n"
            "• Supermarchés (bacs de collecte en entrée)\n"
            "• Déchèteries municipales\n"
            "• Mairies et écoles (collectes ponctuelles)\n"
            "• Magasins spécialisés (pour les batteries de voiture)\n\n"
            "⚠️ **Pourquoi c'est important :**\n"
            "Une seule pile bouton peut polluer **1 m³ de terre** et **500 litres d'eau** pendant 50 ans. "
            "Elles contiennent du mercure, du plomb et du cadmium — très toxiques.\n\n"
            "🇲🇦 **فالمغريب:** كتنحط البطاريات فالسوبرماركيت ولا فالجماعة، ماكينعوش فالزبالة عادي!"
        ),
    },
    {
        "id": "huile",
        "kw_fr": ["huile", "huiles", "huile de cuisson", "huile moteur", "huile usagée", "friture", "frire"],
        "kw_darija": ["زيت", "الزيت", "زيت الطبخ", "زيت المotor", "زيت مستعمل", "زيت ديال الطبخ", "زيت ديال لخبز"],
        "icon": "🛢️",
        "title": "Huiles (cuisine & moteur)",
        "answer": (
            "Les huiles **ne se jettent JAMAIS** dans l'évier ou les toilettes !\n\n"
            "🍳 **Huile de cuisson :**\n"
            "• Filtrer et stocker dans une bouteille fermée\n"
            "• Déposer en déchèterie\n"
            "• Certains supermarchés collectent l'huile usagée\n"
            "1 litre d'huile pollue **1 million de litres d'eau**\n\n"
            "🚗 **Huile moteur :**\n"
            "• Uniquement en déchèterie ou garage agréé\n"
            "• Ne JAMAIS dans la nature, l'évier ou la poubelle\n\n"
            "♻️ **Bon à savoir :** L'huile usagée peut être transformée en biocarburant (diester) !\n\n"
        ),
    },
    {
        "id": "verre",
        "kw_fr": ["verre", "bouteille de verre", "bocal", "flacon", "borne à verre"],
        "kw_darija": ["زجاج", "الزجاج", "قارورة زجاج", "برطمان", "زجاجة"],
        "icon": "🍾",
        "title": "Verre",
        "answer": (
            "Le verre se recycle **à l'infini** sans perte de qualité !\n\n"
            "📋 **Où le déposer :**\n"
            "• Bornes à verre (rues, parkings, supermarchés)\n"
            "• Déchèteries\n\n"
            "✅ **Ce qu'on peut jeter :** Bouteilles, bocaux, flacons (sans bouchon)\n"
            "❌ **Ce qu'on NE jette PAS :** Miroirs, vitres, vaisselle, ampoules, céramique\n\n"
            "💡 **Conseil :** Pas besoin de laver, juste vider le contenu. Retirer les bouchons.\n\n"
            "📊 Le verre met **4000 ans** à se décomposer dans la nature.\n\n"
            "🇲🇦 **فالمغريب:** الزجاج كنناوعو فالكونتينير الزوجاجي اللي كاين فالشوارع."
        ),
    },
    {
        "id": "plastique",
        "kw_fr": ["plastique", "bouteille plastique", "sachet", "film", "emballage plastique", "pvc", "pet"],
        "kw_darija": ["بلاستيك", "البلاستيك", "زجاجة بلاستيك", "ساشيه", "بلاستيك"],
        "icon": "♻️",
        "title": "Plastique",
        "answer": (
            "Le plastique est le déchet le plus problématique au monde.\n\n"
            "📋 **Comment recycler :**\n"
            "• 🟡 Poubelle jaune (bouteilles, flacons avec bouchon)\n"
            "• Rincer avant de jeter\n"
            "• Ne pas écraser les bouteilles\n\n"
            "❌ **Non recyclable en poubelle jaune :**\n"
            "Sachets, film plastique, barquettes souillées, stylos, jouets\n\n"
            "📊 **Chiffres choc :**\n"
            "• 8 millions de tonnes de plastique finissent dans les océans chaque année\n"
            "• Une bouteille met **450 à 1000 ans** à disparaître\n"
            "• Seulement **30%** du plastique est recyclé dans le monde\n\n"
            "🇲🇦 **فالمغريب:** البلاستيك كنناوعو فالصفراء، كانخليو حتا الكابون. "
            "الساشيات والبلاستيك اللي ماينعمش كيماوعو كنخليو فالسوداء."
        ),
    },
    {
        "id": "carton",
        "kw_fr": ["carton", "cartonnette", "boîte en carton", "emballage carton", "rouleau"],
        "kw_darija": ["كارطون", "الكارطون", "كارتون", "الكارتون", "قشرة", "صندوق"],
        "icon": "📦",
        "title": "Carton",
        "answer": (
            "Le carton est l'un des matériaux les plus recyclés au monde !\n\n"
            "📋 **Comment recycler :**\n"
            "• 🟡 Poubelle jaune\n"
            "• **Aplatir** les boîtes pour gagner de la place\n"
            "• Retirer le scotch et les agrafes si possible\n\n"
            "✅ **Recyclable :** Boîtes d'emballage, cartonnettes, rouleaux de papier toilette\n"
            "❌ **Non recyclable :** Carton souillé par la graisse (pizza), carton ciré\n\n"
            "📊 Recycler 1 tonne de carton sauve **17 arbres** et **4000 kWh** d'énergie.\n\n"
            "🇲🇦 **فالمغريب:** الكارطون كنحطو فالصفراء، كنقصوو باش يخلي مكان."
        ),
    },
    {
        "id": "papier",
        "kw_fr": ["papier", "journal", "magazine", "feuille", "cahier", "enveloppe"],
        "kw_darija": ["ورق", "الورق", "جورنال", "مجلة", "كاغد", "الكاغد", "وراق"],
        "icon": "📄",
        "title": "Papier",
        "answer": (
            "Le papier se recycle facilement mais a ses limites.\n\n"
            "📋 **Comment recycler :**\n"
            "• 🟡 Poubelle jaune\n"
            "• Papier propre et sec uniquement\n\n"
            "✅ **Recyclable :** Journaux, magazines, feuilles, enveloppes (sans fenêtre), prospectus\n"
            "❌ **Non recyclable :** Papier essuie-tout, mouchoirs, papier gras, papier calque\n\n"
            "💡 **Bon à savoir :** Le papier ne peut être recyclé que **5 à 7 fois** car les fibres se raccourcissent.\n\n"
            "📊 Recycler 1 tonne de papier économise **26 000 litres d'eau**.\n\n"
            "🇲🇦 **فالمغريب:** الورق النظيف كنحطو فالصفراء. الورق اللي تلوث مكانعوش!"
        ),
    },
    {
        "id": "metal",
        "kw_fr": ["metal", "métal", "aluminium", "canette", "conserve", "fer", "acier", "boîte de conserve"],
        "kw_darija": ["حديد", "الحديد", "معدن", "المعدن", "المنيوم", "قنينة", "علبة", "كنزة", "قزدير"],
        "icon": "🥫",
        "title": "Métal et aluminium",
        "answer": (
            "Le métal est un matériau précieux qui se recycle très bien !\n\n"
            "📋 **Comment recycler :**\n"
            "• 🟡 Poubelle jaune (canettes, boîtes de conserve)\n"
            "• Déchèterie pour les métaux volumineux\n"
            "• Rincer avant de jeter\n\n"
            "📊 **Chiffres impressionnants :**\n"
            "• Recycler 1 canette = assez d'énergie pour **3h de TV**\n"
            "• L'aluminium se recycle **à 95%**\n"
            "• Le recyclage de l'aluminium consomme **95% d'énergie en moins** que la production primaire\n\n"
            "🇲🇦 **فالمغريب:** القنينة والعلبة كنحطو فالصفراء. الحديد الكبير كناوعو للديكوتري."
        ),
    },
    {
        "id": "electronique",
        "kw_fr": ["électronique", "ordinateur", "téléphone", "téléviseur", "écran", "appareil", "DEEE"],
        "kw_darija": ["لكترونيك", "اللكترونيك", "كومبيوتر", "تيليفون", "تيليفيزيون", "شاشة", "جهاز", "الكترونيات"],
        "icon": "💻",
        "title": "Déchets électroniques (DEEE)",
        "answer": (
            "Les déchets électroniques sont les déchets qui augmentent le plus vite au monde !\n\n"
            "📋 **Où les déposer :**\n"
            "• Déchèteries\n"
            "• Magasins spécialisés (reprise en magasin)\n"
            "• Collectes organisées par les mairies\n"
            "• Associations (reconditionnement)\n\n"
            "⚠️ **Interdiction :** Ne JAMAIS jeter dans une poubelle classique\n\n"
            "📊 **Chiffres :**\n"
            "• 50 millions de tonnes de DEEE dans le monde chaque année\n"
            "• Un smartphone contient de l'or, de l'argent, du cuivre, du palladium\n"
            "• 1 tonne de cartes mère = 150 g d'or (valeur ~7000€)\n\n"
            "🇲🇦 **فالمغريب:** الاجهزة اللكترونية كناوعو للديكوتري ولا للمحلات اللي كيعادو يشحنيو."
        ),
    },
    {
        "id": "textile",
        "kw_fr": ["textile", "vêtement", "vêtements", "habit", "habits", "chaussure", "chaussures", "vetement", "don"],
        "kw_darija": ["تيكستيل", "لكسوة", "الكسوة", "حوايج", "الحوايج", "لباس", "اللباس", "صباط", "الصباط"],
        "icon": "👕",
        "title": "Textile et vêtements",
        "answer": (
            "Les vêtements ont une seconde vie !\n\n"
            "📋 **Où les déposer :**\n"
            "• Conteneurs textiles (souvent près des supermarchés)\n"
            "• Associations caritatives (Croix-Rouge, Emmaüs, Secours Populaire)\n"
            "• Déchèteries\n"
            "• Friperies et magasins de seconde main\n\n"
            "✅ **Même troués ou tachés :** Ils peuvent être recyclés en isolant thermique ou chiffons industriels.\n\n"
            "📊 **Chiffres :**\n"
            "• L'industrie textile produit **10% des émissions de CO2** mondiales\n"
            "• Un Français jette en moyenne **12 kg de textile** par an\n\n"
            "🇲🇦 **فالمغريب:** الحوايج كناوعو للجمعيات ولا فالكونتينير اللي كاين فالشوارع."
        ),
    },
    {
        "id": "medicament",
        "kw_fr": ["médicament", "médicaments", "pharmacie", "traitement", "remède"],
        "kw_darija": ["دوا", "الدوا", "أدوية", "الأدوية", "صيدلية", "الصيدلية", "حبوب"],
        "icon": "💊",
        "title": "Médicaments",
        "answer": (
            "Les médicaments périmés **ne vont JAMAIS** dans une poubelle ou les toilettes !\n\n"
            "📋 **Où les déposer :**\n"
            "• **Toute pharmacie** est obligée de reprendre les médicaments périmés\n"
            "• Ils sont collectés via le programme Cyclamed\n\n"
            "✅ **Ce qu'on rapporte :** Médicaments périmés, restes de traitement, emballages\n"
            "💡 **Conseil :** Ne séparez pas le médicament de son emballage\n\n"
            "⚠️ **Pourquoi :** Les médicaments dans l'eau polluent les cours d'eau et menacent la biodiversité.\n\n"
            "🇲🇦 **فالمغريب:** الدوا اللي مخلاص ولا ماكينحتجو ليه كنرجعو للصيدلية، كل صيدلية لازم كتاخو!"
        ),
    },
    {
        "id": "compost",
        "kw_fr": ["compost", "compostage", "bio", "organique", "déchet vert", "restes alimentaires"],
        "kw_darija": ["كومبوست", "الكمبوست", "بقايا الاكل", "بقايا الطعام", "خضرة", "الخضرة", "عضوي"],
        "icon": "🌱",
        "title": "Compostage et déchets organiques",
        "answer": (
            "30% de nos poubelles pourraient être compostés !\n\n"
            "📋 **Ce qu'on peut composter :**\n"
            "• Épluchures de fruits et légumes\n"
            "• Marc de café, sachets de thé\n"
            "• Coquilles d'œufs (écrasées)\n"
            "• Restes de repas (sans viande ni poisson en compostage individuel)\n"
            "• Feuilles mortes, tontes de gazon\n\n"
            "❌ **À éviter :** Viande, poisson, produits laitiers, huile, plastique\n\n"
            "💡 **Où composter :**\n"
            "• Dans votre jardin (composteur individuel)\n"
            "• Compostage collectif de quartier\n"
            "• Certains services municipaux collectent les bio-déchets\n\n"
            "📊 Le compostage réduit le volume des ordures de **30%** et produit un engrais naturel !\n\n"
            "🇲🇦 **فالمغريب:** نقيعو بقايا الاكل والخضرة فحديقة ولا فشربة صغيرة، كيعطي تربة زوينة للفلان!"
        ),
    },
    {
        "id": "decheterie",
        "kw_fr": ["déchèterie", "decheterie", "déchetterie", "dechetterie", "dépôt", "centre de recyclage", "point propre"],
        "kw_darija": ["ديكوتري", "الديكوتري", "مكب", "المكب", "نقطة نظيفة", "مفرغة"],
        "icon": "🏭",
        "title": "Déchèterie",
        "answer": (
            "La déchèterie est le lieu idéal pour tous les déchets qui ne vont pas dans les poubelles classiques.\n\n"
            "📋 **Ce qu'on y dépose :**\n"
            "• Encombrants (meubles, matelas)\n"
            "• Déchets verts (tailles, branchages)\n"
            "• Déchets dangereux (peinture, solvants, huile moteur)\n"
            "• Gravats (petites quantités)\n"
            "• Piles et batteries\n"
            "• Électroménager, électronique\n"
            "• Textiles\n\n"
            "💡 **Accès :** Généralement gratuit pour les particuliers, sur présentation d'un justificatif de domicile.\n\n"
            "📍 **Trouvez la déchèterie la plus proche** dans l'onglet **« Points de collecte »** !"
        ),
    },
    {
        "id": "poubelle_couleur",
        "kw_fr": ["quelle poubelle", "quel bac", "quelle couleur", "poubelle jaune", "poubelle verte", "poubelle noire", "tri selectif", "comment trier", "tri"],
        "kw_darija": ["أي زبالة", "كيفاش نطري", "التطري", "الصفراء", "السوداء", "الخضراء", "الزرقاء"],
        "icon": "🗑️",
        "title": "Guide des couleurs de poubelles",
        "answer": (
            "Le guide complet du tri sélectif :\n\n"
            "🟡 **Poubelle jaune** → Emballages\n"
            "• Carton, papier, plastique (bouteilles, flacons)\n"
            "• Métal (canettes, boîtes de conserve)\n\n"
            "🟢 **Poubelle verte** (ou bleue selon la ville) → Verre\n"
            "• Bouteilles, bocaux, flacons en verre\n\n"
            "⚫ **Poubelle noire/grise** → Déchets ménagers\n"
            "• Restes alimentaires, mouchoirs, couches\n"
            "• Tout ce qui n'est pas recyclable\n\n"
            "🟤 **Poubelle marron** → Bio-déchets (dans certaines villes)\n"
            "• Épluchures, restes de repas\n\n"
            "🇲🇦 **فالمغريب:** الصفراء للكارطون والورق والبلاستيك والمعادن. الخضراء للزجاج. السوداء للباقي."
        ),
    },
    {
        "id": "ampoule",
        "kw_fr": ["ampoule", "ampoules", "néon", "fluorescente", "LED", "lampe"],
        "kw_darija": ["لمبة", "اللمبة", "نيون", "لمبات"],
        "icon": "💡",
        "title": "Ampoules et lampes",
        "answer": (
            "Toutes les ampoules ne se recyclent pas de la même façon !\n\n"
            "💡 **LED et halogènes :**\n"
            "• Poubelle classique (pas de substances dangereuses)\n"
            "• Ou mieux : déchèterie pour recyclage des composants\n\n"
            "⚠️ **Fluocompactes et néons (avec le logo « DEEE ») :**\n"
            "• **Obligatoirement en déchèterie** ou en magasin\n"
            "• Contiennent du mercure — très toxiques\n\n"
            "❌ **Incandescence (anciennes) :** Poubelle classique\n\n"
            "🇲🇦 **فالمغريب:** اللمبات العادية فالزبالة العادية. اللمبات اللي كاين فيها مركوري كناوعو للديكوطري!"
        ),
    },
    {
        "id": "meuble",
        "kw_fr": ["meuble", "meubles", "canapé", "table", "armoire", "encombrant", "encombrants", "matelas"],
        "kw_darija": ["طومبل", "الطومبل", "موبليا", "الموبليا", "كنبة", "طاولة", "دوالية", "فراش"],
        "icon": "🪑",
        "title": "Meubles et encombrants",
        "answer": (
            "Les meubles ne vont JAMAIS dans une poubelle classique !\n\n"
            "📋 **Solutions :**\n"
            "• 🏭 **Déchèterie** (gratuit pour les particuliers)\n"
            "• 📅 **Enlèvement par la mairie** (prendre RDV, parfois gratuit)\n"
            "• 🔄 **Don** (Emmaüs, Le Relais, associations)\n"
            "• 📱 **Applications de don** (Donnons, Geev)\n\n"
            "💡 **Bon à savoir :** Un meuble en bon état peut avoir une seconde vie !\n\n"
            "🇲🇦 **فالمغريب:** الطومبل اللي مكيعادش يخدم كنعطيو للجمعيات (أماوس). كاين شي فراق كيستافدو منو!"
        ),
    },
    {
        "id": "peinture",
        "kw_fr": ["peinture", "peintures", "solvant", "solvants", "vernis", "white spirit", "produit chimique", "produit dangereux"],
        "kw_darija": ["صباغة", "الصباغة", "سولفان", "السولفان", "فارني", "مادة كيميائية", "منتج خطر"],
        "icon": "🎨",
        "title": "Peintures et produits chimiques",
        "answer": (
            "Les produits chimiques sont des **déchets dangereux** (DD) !\n\n"
            "📋 **Où les déposer :**\n"
            "• **Déchèterie** (seul lieu autorisé)\n"
            "• Certains magasins de bricolage reprennent les peintures\n\n"
            "⚠️ **Interdiction absolue :**\n"
            "• Évier, toilettes, égouts\n"
            "• Poubelle classique\n"
            "• Dans la nature\n\n"
            "💡 **Conseil :** Achetez la juste quantité. Un pot de peinture non ouvert peut se garder 10 ans !\n\n"
            "🇲🇦 **فالمغريب:** الصباغة والسولفان كناوعو غير للديكوطري، خطير على الصحة والبيئة!"
        ),
    },
    {
        "id": "pourquoi_recycler",
        "kw_fr": ["pourquoi recycler", "intérêt du recyclage", "à quoi ça sert", "utilité", "avantage", "pourquoi trier", "importance"],
        "kw_darija": ["علاش نطري", "علاش نعاود", "أش كاين الفايدة", "الفائدة", "المزايا", "لماذا"],
        "icon": "🌍",
        "title": "Pourquoi recycler ?",
        "answer": (
            "Recycler, c'est agir concrètement pour la planète !\n\n"
            "📊 **Chiffres clés :**\n"
            "• Réduction des émissions de CO2 de **30 à 70%** selon le matériau\n"
            "• Économie de matières premières (pétrole, minerais, bois)\n"
            "• Création d'emplois : le recyclage crée **10x plus d'emplois** que l'incinération\n\n"
            "💰 **Économie :**\n"
            "• 1 tonne d'aluminium recyclée = **6 tonnes de bauxite** économisées\n"
            "• 1 tonne de papier recyclé = **26 000 litres d'eau** économisés\n"
            "• 1 tonne de verre recyclé = **700 kg de sable** économisés\n\n"
            "🏠 **Au quotidien :** Le tri sélectif est un geste simple qui a un **vrai impact**.\n\n"
            "🇲🇦 **فالمغريب:** التطري كيقلل التلوث ويصايب البيئة. كلشي كنطرّيو كايقلل الكاربون!"
        ),
    },
    {
        "id": "maroc",
        "kw_fr": ["maroc", "marrakech", "casablanca", "rabat", "fès", "fes", "tanger", "agadir", "oujda", "marocaine"],
        "kw_darija": ["المغرب", "مراكش", "الدار البيضا", "رباط", "فاس", "طنجة", "أكادير", "وجدة", "المغربي", "لمغرب"],
        "icon": "🇲🇦",
        "title": "Recyclage au Maroc",
        "answer": (
            "Le Maroc est devenu un acteur majeur du recyclage en Afrique !\n\n"
            "📋 **Le recyclage au Maroc :**\n"
            "• **Plastique :** Le Maroc est le 2ème recycleur de plastique en Afrique\n"
            "• **Piles :** Collecte via des bacs dans les supermarchés et écoles\n"
            "• **Verre :** Bornes dans les grandes villes\n"
            "• **Électronique :** Programmes de collecte en développement\n\n"
            "🏛️ **Cadre légal :**\n"
            "• Loi 28-00 relative à la gestion des déchets\n"
            "• Programme National des Déchets Ménagers (PNDM)\n"
            "• Interdiction des sacs plastiques depuis 2016\n\n"
            "🔄 **Initiatives :**\n"
            "• ECOLED (collecte piles dans les écoles)\n"
            "• Programme MEDALOUR (huiles usagées)\n\n"
            "💡 **Conseil :** Utilisez l'onglet **« Points de collecte »** pour trouver les centres proches de chez vous !"
        ),
    },
    {
        "id": "salutation",
        "kw_fr": ["bonjour", "salut", "bonsoir", "hello", "hi", "coucou", "hey"],
        "kw_darija": ["سلام", "السلام", "مرحبا", "سلاو", "كيفاش", "لاباس", "واش كاين"],
        "icon": "👋",
        "title": "Bienvenue !",
        "answer": (
            "مرحبا بك ! 👋\n\n"
            "أنا **EcoBot**, مساعدك البيئي ! كنفهم بالفرانساوية والدارجة. 🇲🇦\n\n"
            "Bonjour ! Je suis **EcoBot**, votre assistant écologique !\n\n"
            "Posez-moi vos questions sur le recyclage :\n"
            "• 🔋 *Où jeter les piles ?*\n"
            "• 🛢️ *Comment recycler les huiles moteur ?*\n"
            "• 🗑️ *Quelle poubelle pour le plastique ?*\n"
            "• 🇲🇦 *كنعيط الزجاج فين ؟*"
        ),
    },
    {
        "id": "merci",
        "kw_fr": ["merci", "super", "génial", "parfait", "excellent", "bravo", "cool", "nickel", "chouette"],
        "kw_darija": ["شكرا", "شكراً", "بارك الله فيك", "مزيان", "واخا", "يعطيك الصحة", "الله يبارك"],
        "icon": "😊",
        "title": "Merci !",
        "answer": (
            "شكرا لك ! 😊 الله يعطيك الصحة.\n\n"
            "Le geste le plus simple pour la planète, c'est **trier correctement** chaque jour. "
            "Chaque geste compte ! 🌍💚\n\n"
            "Si tu as d'autres questions, n'hésite pas !"
        ),
    },
    {
        "id": "pneu",
        "kw_fr": ["pneu", "pneus", "pneumatique", "roue"],
        "kw_darija": ["طيارة", "الطيارة", "عجلة", "العجلة"],
        "icon": "🛞",
        "title": "Pneus",
        "answer": (
            "Les pneus sont des **déchets industriels spéciaux** !\n\n"
            "📋 **Où les déposer :**\n"
            "• Garagiste (reprise souvent gratuite)\n"
            "• Déchèterie\n"
            "• Collectes organisées par les mairies\n\n"
            "❌ **Interdiction absolue :** Décharge sauvage, brûlage (très toxique !)\n\n"
            "♻️ **Recyclage :** Granulats pour terrains de sport, bacs à fleurs, revêtements de sol\n\n"
            "🇲🇦 **فالمغريب:** الطيارات كناوعو للجاراج ولا للديكوطري. حرام يطرحو فالطبيعة ولا يحرقو!"
        ),
    },
]

CITIES_MAROC = {
    "fès": "فاس", "fes": "فاس",
    "casablanca": "الدار البيضا", "casa": "الدار البيضا",
    "rabat": "الرباط", "marrakech": "مراكش", "tanger": "طنجة",
    "agadir": "أكادير", "oujda": "وجدة", "meknès": "مكناس", "meknes": "مكناس",
    "kénitra": "القنيطرة", "kenitra": "القنيطرة", "tétouan": "تطوان", "tetouan": "تطوان",
    "safi": "سفي", "el jadida": "الجديدة", "nador": "الناظور", "beni mellal": "بني ملال",
}
CITIES_FR = {
    "paris": "Paris", "lyon": "Lyon", "marseille": "Marseille", "toulouse": "Toulouse",
    "nice": "Nice", "nantes": "Nantes", "strasbourg": "Strasbourg", "montpellier": "Montpellier",
    "bordeaux": "Bordeaux", "lille": "Lille", "rennes": "Rennes",
}

# ── SUGGESTIONS (plain text, used with st.button) ──
SUGGESTIONS_FR = [
    ("🔋", "Où jeter les piles à Fès ?"),
    ("🛢️", "Comment recycler les huiles moteur ?"),
    ("🗑️", "Quelle poubelle pour le plastique ?"),
    ("💊", "Que faire des médicaments périmés ?"),
    ("🌱", "Comment composter à la maison ?"),
    ("🇲🇦", "Le recyclage au Maroc"),
]
SUGGESTIONS_DARIJA = [
    ("🔋", " ؟"),
    ("🍾", "كيعيط الزجاج فين ؟"),
    ("💊", "كيعيط الدوا المخلاص فين ؟"),
    ("🌍", "علاش نطري ؟"),
    ("🛢️", "كيعيط الزيت فين ؟"),
    ("🇲🇦", "التطري فالمغريب كيماشي ؟"),
]

# ══════════════════════════════════════════════
# HISTORIQUE
# ══════════════════════════════════════════════
HISTORY_FILE = "classification_history.json"

def charger_historique():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []
    return []

def sauvegarder_historique(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def ajouter_entree(classe, confiance):
    history = charger_historique()
    history.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "classe": classe, "confiance": round(float(confiance), 2),
        "recyclable": INFOS[classe]["recyclable"],
        "poubelle": INFOS[classe]["poubelle"], "emoji": INFOS[classe]["emoji"],
    })
    sauvegarder_historique(history)

# ══════════════════════════════════════════════
# CHATBOT ENGINE
# ══════════════════════════════════════════════
def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]

def trouver_ville(question):
    q = question.lower().strip()
    for fr, ar in CITIES_MAROC.items():
        if fr in q:
            return f"{ar} ({fr.capitalize()})", "maroc"
    for fr, ar in CITIES_FR.items():
        if fr in q:
            return fr.capitalize(), "france"
    for fr, ar in CITIES_MAROC.items():
        if ar in q:
            return f"{ar} ({fr.capitalize()})", "maroc"
    return None, None

def trouver_reponse_chatbot(question):
    if not question or not question.strip():
        return None, 0.0
    q = question.lower().strip()
    mots = q.replace("?", "").replace("!", "").replace(".", "").replace(",", " ").split()
    best_score = 0.0
    best_entry = None
    ville_info, pays = trouver_ville(question)

    for entry in CHATBOT_KB:
        score = 0.0
        for kw in entry["kw_fr"]:
            if kw in q:
                score += 3.0
        for kw in entry["kw_darija"]:
            if kw in q:
                score += 3.0
        for mot in mots:
            if len(mot) < 2:
                continue
            for kw in entry["kw_fr"] + entry["kw_darija"]:
                if mot in kw or kw in mot:
                    score += 0.5
        for mot in mots:
            if len(mot) < 3:
                continue
            for kw in entry["kw_fr"] + entry["kw_darija"]:
                dist = levenshtein(mot, kw)
                max_len = max(len(mot), len(kw))
                if max_len > 0 and dist / max_len < 0.3:
                    score += 0.8
        if score > best_score:
            best_score = score
            best_entry = entry

    if best_score < 1.0:
        return None, best_score

    answer = best_entry["answer"]
    if ville_info and best_entry["id"] not in ("salutation", "merci"):
        answer += (
            f"\n\n---\n📍 **Pour {ville_info}** : "
            "Utilisez l'onglet **« Points de collecte »** pour trouver "
            "les centres de recyclage les plus proches de votre ville !"
        )
    hist = charger_historique()
    if hist:
        dernier = hist[-1]["classe"]
        if dernier != "trash" and best_entry["id"] == dernier:
            answer += (
                f"\n\n💡 *D'après votre dernière classification ({INFOS[dernier]['emoji']} {dernier}), "
                f"ce déchet va dans **{INFOS[dernier]['poubelle']}**.*"
            )
    return answer, best_score

def generer_reponse_defaut(question):
    ville_info, pays = trouver_ville(question)
    if ville_info:
        return (
            f"🤔 Je n'ai pas trouvé d'information spécifique pour cette question.\n\n"
            f"📍 **Pour {ville_info}** : Utilisez l'onglet **« Points de collecte »** "
            f"pour trouver les centres de recyclage les plus proches.\n\n"
            f"Exemples de questions :\n"
            f"• 🔋 *Où jeter les piles ?*\n"
            f"• 🛢️ *Comment recycler les huiles ?*\n"
            f"• 🗑️ *Quelle poubelle pour le plastique ?*"
        )
    return (
        "🤔 Je n'ai pas bien compris votre question.\n\n"
        "Voici des exemples :\n\n"
        "🔋 *« Où jeter les piles à Fès ? »*\n"
        "🛢️ *« Comment recycler les huiles moteur ? »*\n"
        "💊 *« Où déposer les médicaments ? »*\n"
        "🗑️ *« Quelle poubelle pour le carton ? »*\n"
        "🌍 *« Pourquoi recycler ? »*\n\n"
        "🇲🇦 **بالدارجة :**\n"
      
        "• *«  ؟ »*\n"
        "• *« »*"
    )

# ══════════════════════════════════════════════
# CHARGEMENT MODÈLE
# ══════════════════════════════════════════════
@st.cache_resource
def charger_modele():
    return tf.keras.models.load_model("model/mobilenetv2.keras")

# ══════════════════════════════════════════════
# GRAD-CAM
# ══════════════════════════════════════════════
def generer_gradcam(model, img_array, class_idx):
    base_model = None
    for layer in model.layers:
        if isinstance(layer, tf.keras.Model):
            base_model = layer
            break
    if base_model is None:
        st.error("Backbone CNN introuvable")
        return None
    last_conv_layer = None
    for layer in reversed(base_model.layers):
        if isinstance(layer, tf.keras.layers.Conv2D):
            last_conv_layer = layer
            break
    if last_conv_layer is None:
        st.error("Aucune couche Conv2D trouvée")
        return None
    grad_model = tf.keras.models.Model(
        inputs=model.inputs,
        outputs=[last_conv_layer.output, model.output]
    )
    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(img_array)
        loss = predictions[:, class_idx]
    grads = tape.gradient(loss, conv_outputs)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    conv_outputs = conv_outputs[0]
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    heatmap = tf.maximum(heatmap, 0)
    max_val = tf.reduce_max(heatmap)
    if max_val == 0:
        return np.zeros((7, 7))
    heatmap /= max_val
    return heatmap.numpy()

def superposer_gradcam(image, heatmap, alpha=0.4):
    img_np = np.array(image.resize((224, 224)))
    heatmap_resized = cv2.resize(heatmap, (224, 224))
    heatmap_colored = cv2.applyColorMap(np.uint8(255 * heatmap_resized), cv2.COLORMAP_JET)
    heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
    superimposed = (heatmap_colored * alpha + img_np * (1 - alpha)).astype(np.uint8)
    return Image.fromarray(superimposed)

# ══════════════════════════════════════════════
# GÉOLOCALISATION
# ══════════════════════════════════════════════
def geocoder_adresse(adresse, country="fr"):
    params = urllib.parse.urlencode({
        "q": adresse, "format": "json", "limit": "1",
        "countrycodes": country, "addressdetails": "1", "accept-language": "fr",
    })
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "EcoScanAI/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"]), data[0].get("display_name", "")
    except Exception:
        pass
    return None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

@st.cache_data(ttl=1800, show_spinner=False)
def trouver_centres(lat, lon, rayon_km=5, filtre_type=None, mode="tous"):
    delta = rayon_km / 111.0

    if mode == "centres":
        # ── UNIQUEMENT les vrais centres : déchèteries + centres de recyclage ──
        query = (
            f"[out:json][timeout:25];\n(\n"
            f'  node["amenity"="waste_disposal"]({lat-delta},{lon-delta},{lat+delta},{lon+delta});\n'
            f'  way["amenity"="waste_disposal"]({lat-delta},{lon-delta},{lat+delta},{lon+delta});\n'
            f'  node["amenity"="recycling"]["recycling_type"="centre"]({lat-delta},{lon-delta},{lat+delta},{lon+delta});\n'
            f'  way["amenity"="recycling"]["recycling_type"="centre"]({lat-delta},{lon-delta},{lat+delta},{lon+delta});\n'
            f");\nout center;"
        )
    else:
        # ── TOUS les points : conteneurs de rue + centres ──
        query = (
            f"[out:json][timeout:25];\n(\n"
            f'  node["amenity"="recycling"]({lat-delta},{lon-delta},{lat+delta},{lon+delta});\n'
            f'  way["amenity"="recycling"]({lat-delta},{lon-delta},{lat+delta},{lon+delta});\n'
            f'  node["amenity"="waste_disposal"]({lat-delta},{lon-delta},{lat+delta},{lon+delta});\n'
            f'  way["amenity"="waste_disposal"]({lat-delta},{lon-delta},{lat+delta},{lon+delta});\n'
            f");\nout center;"
        )

    overpass_urls = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    ]
    data = None
    for api_url in overpass_urls:
        req = urllib.request.Request(
            api_url, data=query.encode("utf-8"),
            headers={"User-Agent": "EcoScanAI/1.0"}
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except Exception:
            continue

    if data is None:
        return []

    results = []
    for elem in data.get("elements", []):
        if elem["type"] == "node":
            elat, elon = elem["lat"], elem["lon"]
        elif elem["type"] == "way" and "center" in elem:
            elat, elon = elem["center"]["lat"], elem["center"]["lon"]
        else:
            continue

        tags = elem.get("tags", {})
        dist = haversine(lat, lon, elat, elon)
        if dist > rayon_km:
            continue

        # ── Classification précise du type de point ──
        amenity = tags.get("amenity", "")
        recycling_type = tags.get("recycling_type", "")
        is_decheterie = (amenity == "waste_disposal")
        is_centre = (recycling_type == "centre")

        # Nom intelligent
        if is_decheterie:
            nom = tags.get("name", "Déchèterie")
        elif is_centre:
            nom = tags.get("name", "Centre de recyclage")
        else:
            nom = tags.get("name", "Point de recyclage")

        # Type label
        if is_decheterie:
            type_label = "🏭 Déchèterie"
        elif is_centre:
            type_label = "🏭 Centre de recyclage"
        elif recycling_type == "container":
            type_label = "🟢 Conteneur"
        elif recycling_type == "overground":
            type_label = "🔵 Point surélevé"
        elif recycling_type == "underground":
            type_label = "⚫ Point enterré"
        else:
            type_label = "♻️ Point de recyclage"

        # Adresse
        rue = tags.get("addr:street", "")
        num = tags.get("addr:housenumber", "")
        cp = tags.get("addr:postcode", "")
        ville = tags.get("addr:city", "")
        adresse_parts = [p for p in [num, rue, cp, ville] if p]
        adresse = ", ".join(adresse_parts) if adresse_parts else "Adresse non renseignée"

        # Types de déchets acceptés
        types_acceptes = []
        for k, v in tags.items():
            if k.startswith("recycling:") and v == "yes":
                tag_name = k.replace("recycling:", "")
                types_acceptes.append(TAG_LABELS.get(tag_name, tag_name))

        # Heures d'ouverture
        horaires = tags.get("opening_hours", "")

        # Téléphone
        telephone = tags.get("phone", tags.get("contact:phone", ""))

        # Site web
        website = tags.get("website", tags.get("contact:website", ""))

        results.append({
            "nom": nom,
            "type": type_label,
            "is_decheterie": is_decheterie,
            "is_centre": is_centre,
            "adresse": adresse,
            "distance": round(dist, 2),
            "lat": elat,
            "lon": elon,
            "tags": tags,
            "types_acceptes": types_acceptes,
            "types_acceptes_str": " · ".join(types_acceptes) if types_acceptes else "Non précisé",
            "horaires": horaires,
            "telephone": telephone,
            "website": website,
            "walking_min": int(dist / 0.083),
            "driving_min": int(dist / 0.5),
        })

    # ── Filtrer par type de déchet si demandé ──
    if filtre_type and filtre_type in RECYCLING_FILTERS and RECYCLING_FILTERS[filtre_type]:
        required = RECYCLING_FILTERS[filtre_type]
        filtered = [r for r in results if any(r["tags"].get(t) == "yes" for t in required)]
        results = filtered  # Toujours appliquer le filtre, même si vide

    results.sort(key=lambda x: x["distance"])
    return results


# ══════════════════════════════════════════════
# CARTE HTML (FOLIUM-LIKE)
# ══════════════════════════════════════════════
def generer_carte_html(user_lat, user_lon, centres):
    """Génère une carte HTML interactive avec les points de collecte."""

    # Couleurs par type
    def get_color(centre):
        if centre["is_decheterie"]:
            return "#EF4444"  # Rouge pour déchèterie
        elif centre["is_centre"]:
            return "#6366F1"  # Indigo pour centre
        else:
            return "#10B981"  # Vert pour conteneur

    def get_icon(centre):
        if centre["is_decheterie"]:
            return "🏭"
        elif centre["is_centre"]:
            return "♻️"
        else:
            return "🟢"

    # Construire les marqueurs
    markers_js = []
    for i, c in enumerate(centres[:50]):  # Limiter à 50 marqueurs
        color = get_color(c)
        icon = get_icon(c)
        types_str = " · ".join(c["types_acceptes"][:5]) if c["types_acceptes"] else "Non précisé"
        popup_html = f"""
        <div style="font-family:Arial,sans-serif;min-width:220px;">
            <h4 style="margin:0 0 8px;color:{color};">{icon} {c['nom']}</h4>
            <p style="margin:4px 0;font-size:13px;"><b>📍</b> {c['adresse']}</p>
            <p style="margin:4px 0;font-size:12px;color:#666;"><b>Type:</b> {c['type']}</p>
            <p style="margin:4px 0;font-size:12px;color:#666;"><b>Distance:</b> {c['distance']} km</p>
            <p style="margin:4px 0;font-size:11px;color:#888;"><b>Accepte:</b> {types_str}</p>
            <a href="https://www.google.com/maps/dir/?api=1&destination={c['lat']},{c['lon']}" 
               target="_blank" style="color:#10B981;font-size:12px;">🗺️ Itinéraire</a>
        </div>
        """
        markers_js.append(f"""
            var marker{i} = L.marker([{c['lat']}, {c['lon']}]).addTo(map);
            marker{i}.bindPopup({json.dumps(popup_html)});
            marker{i}.setIcon(L.divIcon({{
                className: 'custom-marker',
                html: '<div style="background:{color};width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3);">{icon}</div>',
                iconSize: [28, 28],
                iconAnchor: [14, 14]
            }}));
        """)

    markers_js_str = "\n".join(markers_js)

    # Calculer les bounds
    if centres:
        lats = [user_lat] + [c["lat"] for c in centres]
        lons = [user_lon] + [c["lon"] for c in centres]
        bounds = f"[[{min(lats)-0.01}, {min(lons)-0.01}], [{max(lats)+0.01}, {max(lons)+0.01}]]"
    else:
        bounds = f"[[{user_lat-0.05}, {user_lon-0.05}], [{user_lat+0.05}, {user_lon+0.05}]]"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            body {{ margin: 0; padding: 0; }}
            #map {{ width: 100%; height: 100%; min-height: 500px; border-radius: 12px; }}
            .leaflet-popup-content-wrapper {{ border-radius: 12px; }}
            .custom-marker {{ background: transparent !important; border: none !important; }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var map = L.map('map').fitBounds({bounds});
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> contributors',
                maxZoom: 19
            }}).addTo(map);

            // Marqueur utilisateur
            var userMarker = L.marker([{user_lat}, {user_lon}]).addTo(map);
            userMarker.setIcon(L.divIcon({{
                className: 'custom-marker',
                html: '<div style="background:#3B82F6;width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:18px;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.4);">📍</div>',
                iconSize: [36, 36],
                iconAnchor: [18, 18]
            }}));
            userMarker.bindPopup("<b>Votre position</b>");

            {markers_js_str}
        </script>
    </body>
    </html>
    """
    return html

# ══════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@400;700;800&display=swap');

/* ── Palette Claire Sage & Cream ──
   --clr-bg:       #F5F5DC  (crème — fond principal)
   --clr-surface:  #FAFAF0  (blanc cassé — cartes/surfaces)
   --clr-surface2: #EFF0E3  (crème légèrement plus foncé)
   --clr-primary:  #6B8F5E  (vert sauge foncé — textes actifs, accents)
   --clr-accent:   #9CAF88  (vert sauge medium — boutons, badges)
   --clr-text:     #3A4A30  (vert très foncé — texte principal)
   --clr-muted:    #7A8C6E  (vert moyen — texte secondaire)
   --clr-border:   rgba(156,175,136,0.4) (bordures)
*/

.stApp { background: #F5F5DC !important; color: #3A4A30 !important; }
* { font-family: 'Space Grotesk', sans-serif !important; }

.hero-title {
    font-family: 'Syne', sans-serif !important; font-size: 64px; font-weight: 800;
    background: linear-gradient(135deg, #4A6B3A 0%, #9CAF88 50%, #4A6B3A 100%);
    background-size: 200% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; animation: gradShift 4s linear infinite;
    text-align: center; letter-spacing: -2px; line-height: 1.1;
}
.hero-sub { text-align: center; color: #7A8C6E; font-size: 17px; margin: 8px 0 0; font-weight: 300; }
.hero-badge { display: block; text-align: center; margin-bottom: 14px; }
.hero-badge span {
    background: rgba(156,175,136,0.2); border: 1px solid rgba(156,175,136,0.5);
    color: #5A7A4A; padding: 5px 18px; border-radius: 50px;
    font-size: 12px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase;
}
@keyframes gradShift { 0%{background-position:0% center;} 100%{background-position:200% center;} }

.result-box { background:#FAFAF0; border:1px solid rgba(156,175,136,0.35); border-radius:24px; padding:32px; text-align:center; box-shadow:0 2px 16px rgba(156,175,136,0.15); }
.result-emoji { font-size:72px; display:block; margin-bottom:8px; }
.result-class { font-family:'Syne',sans-serif!important; font-size:40px; font-weight:800; text-transform:uppercase; letter-spacing:-1px; margin:4px 0; color:#3A4A30; }
.confidence-badge { display:inline-block; background:rgba(156,175,136,0.2); border:1px solid rgba(156,175,136,0.5); color:#5A7A4A; border-radius:50px; padding:7px 22px; font-size:22px; font-weight:700; margin:10px 0; }
.bin-tag { display:inline-block; border-radius:10px; padding:8px 20px; font-weight:600; font-size:15px; margin-top:12px; }
.stat-row { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin-top:18px; }
.stat-box { background:#FAFAF0; border:1px solid rgba(156,175,136,0.3); border-radius:14px; padding:14px 10px; text-align:center; box-shadow:0 1px 6px rgba(156,175,136,0.1); }
.stat-val { font-family:'Syne',sans-serif!important; font-size:20px; font-weight:700; color:#5A7A4A; }
.stat-lbl { font-size:11px; color:#7A8C6E; text-transform:uppercase; letter-spacing:1px; margin-top:3px; }
.info-card { background:#FAFAF0; border:1px solid rgba(156,175,136,0.3); border-radius:14px; padding:16px 18px; margin-top:12px; }
.info-card-lbl { font-size:11px; text-transform:uppercase; letter-spacing:1.5px; color:#7A8C6E; margin-bottom:6px; }
.info-card-val { font-size:14px; color:#4A5E3A; line-height:1.6; }
.funfact-box { background:linear-gradient(135deg,rgba(156,175,136,0.12),rgba(245,245,220,0.6)); border:1px solid rgba(156,175,136,0.35); border-radius:14px; padding:18px; margin-top:12px; }
.top5-item { margin-bottom:13px; }
.top5-label { display:flex; justify-content:space-between; font-size:13px; margin-bottom:5px; color:#7A8C6E; }
.bar-bg { background:rgba(156,175,136,0.2); border-radius:50px; height:7px; overflow:hidden; }
.bar-fill { height:100%; border-radius:50px; }
.sec-hdr { display:flex; align-items:center; gap:10px; margin:0 0 18px; padding-bottom:14px; border-bottom:1px solid rgba(156,175,136,0.3); }
.sec-dot { width:7px; height:7px; border-radius:50%; background:#9CAF88; box-shadow:0 0 7px rgba(156,175,136,0.5); flex-shrink:0; }
.sec-title { font-family:'Syne',sans-serif!important; font-size:18px; font-weight:700; color:#3A4A30; }
.tag-oui { color:#4A6B3A; background:rgba(156,175,136,0.2); border:1px solid rgba(156,175,136,0.45); border-radius:50px; padding:3px 12px; font-size:12px; font-weight:600; }
.tag-non { color:#C0392B; background:rgba(192,57,43,0.08); border:1px solid rgba(192,57,43,0.2); border-radius:50px; padding:3px 12px; font-size:12px; font-weight:600; }
.sidebar-logo { display:flex; align-items:center; gap:10px; padding:10px 0 16px; }
.sidebar-logo-text { font-family:'Syne',sans-serif!important; font-size:18px; font-weight:700; color:#3A4A30!important; }
.class-pill { display:flex; align-items:center; gap:8px; background:rgba(156,175,136,0.1); border:1px solid rgba(156,175,136,0.25); border-radius:8px; padding:8px 12px; margin:4px 0; font-size:13px; color:#3A4A30; }
.rc-card { background:#FAFAF0; border:1px solid rgba(156,175,136,0.3); border-radius:16px; padding:20px; margin-bottom:12px; box-shadow:0 1px 8px rgba(156,175,136,0.1); }
.rc-card-decheterie { border-color:rgba(192,57,43,0.25)!important; }
.rc-card-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px; }
.rc-card-name { font-weight:700; font-size:16px; color:#3A4A30; }
.rc-card-type { font-size:12px; padding:3px 10px; border-radius:50px; font-weight:600; }
.rc-card-addr { font-size:13px; color:#7A8C6E; margin-bottom:10px; }
.rc-card-types { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:12px; }
.rc-type-pill { font-size:11px; padding:3px 10px; border-radius:50px; background:rgba(156,175,136,0.15); border:1px solid rgba(156,175,136,0.3); color:#5A7A4A; font-weight:500; }
.rc-card-footer { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; }
.rc-distance { font-size:13px; color:#7A8C6E; }
.rc-distance strong { color:#5A7A4A; font-size:18px; font-weight:800; }
.rc-links { display:flex; gap:6px; }
.rc-link { font-size:12px; padding:5px 14px; border-radius:8px; text-decoration:none; font-weight:600; display:inline-flex; align-items:center; gap:4px; }
.rc-link-nav { background:rgba(156,175,136,0.18); border:1px solid rgba(156,175,136,0.4); color:#4A6B3A; }
.rc-link-osm { background:rgba(106,141,90,0.12); border:1px solid rgba(106,141,90,0.3); color:#5A7A4A; }
.rc-search-hint { background:rgba(156,175,136,0.1); border:1px solid rgba(156,175,136,0.25); border-radius:12px; padding:14px 18px; margin-top:12px; }
.rc-search-hint-title { font-size:12px; font-weight:700; color:#5A7A4A; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px; }
.rc-search-hint-text { font-size:13px; color:#7A8C6E; line-height:1.6; }
/* Chat */
.chat-welcome-box {
    background: linear-gradient(135deg, rgba(156,175,136,0.15), rgba(245,245,220,0.8));
    border: 1px solid rgba(156,175,136,0.35); border-radius: 20px;
    padding: 28px; text-align: center; margin-bottom: 20px;
}
[data-testid="stSidebar"] { background:#EFF0E3!important; border-right:1px solid rgba(156,175,136,0.3)!important; }
[data-testid="stSidebar"] * { color:#3A4A30!important; }
.stTabs [data-baseweb="tab-list"] { background:#EFF0E3!important; border-radius:12px!important; padding:5px!important; border:1px solid rgba(156,175,136,0.3)!important; gap:4px!important; }
.stTabs [data-baseweb="tab"] { color:#7A8C6E!important; border-radius:8px!important; padding:9px 18px!important; font-weight:500!important; }
.stTabs [aria-selected="true"] { background:rgba(156,175,136,0.25)!important; color:#4A6B3A!important; border:1px solid rgba(156,175,136,0.45)!important; }
.stButton > button { background:rgba(156,175,136,0.18)!important; border:1px solid rgba(156,175,136,0.45)!important; color:#4A6B3A!important; border-radius:10px!important; font-weight:600!important; }
.stButton > button:hover { background:rgba(156,175,136,0.3)!important; }
.stDownloadButton > button { background:rgba(106,141,90,0.12)!important; border:1px solid rgba(106,141,90,0.35)!important; color:#5A7A4A!important; border-radius:10px!important; font-weight:600!important; }
[data-testid="stMetric"] { background:#FAFAF0!important; border:1px solid rgba(156,175,136,0.3)!important; border-radius:14px!important; padding:16px!important; box-shadow:0 1px 6px rgba(156,175,136,0.1)!important; }
[data-testid="stMetricValue"] { color:#5A7A4A!important; }
[data-testid="stMetricLabel"] { color:#7A8C6E!important; }
[data-testid="stFileUploader"] > div { border:2px dashed rgba(156,175,136,0.4)!important; border-radius:14px!important; background:rgba(156,175,136,0.06)!important; }
[data-testid="stChatMessageContent"] p,
[data-testid="stChatMessageContent"] li,
[data-testid="stChatMessageContent"] strong,
[data-testid="stChatMessageContent"] em,
[data-testid="stChatMessageContent"] a { color: #000000 !important; }
#MainMenu { visibility:hidden; } footer { visibility:hidden; } header { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown("""<div class="sidebar-logo"><span style="font-size:26px;">♻️</span><span class="sidebar-logo-text">EcoScan AI</span></div>""", unsafe_allow_html=True)
    st.divider()
    st.markdown("**⚙️ Options**")
    afficher_gradcam = st.toggle("🔥 Grad-CAM", value=True)
    afficher_top5    = st.toggle("📊 Top 5", value=True)
    afficher_impact  = st.toggle("🌍 Impact écologique", value=True)
    afficher_funfact = st.toggle("💡 Fun Facts", value=True)
    afficher_carte   = st.toggle("🗺️ Carte recyclage", value=True)
    st.divider()
    st.markdown("**🗂️ Classes**")
    for c, info in INFOS.items():
        rec = '<span class="tag-oui">♻️</span>' if info["recyclable"] else '<span class="tag-non">✗</span>'
        st.markdown(f"""<div class="class-pill"><span>{info['emoji']}</span><span style="flex:1;text-transform:capitalize;">{c}</span>{rec}</div>""", unsafe_allow_html=True)
    st.divider()
    nb = len(charger_historique())
    st.markdown(f"""<div style="text-align:center;padding:14px;background:rgba(156,175,136,0.15);border:1px solid rgba(156,175,136,0.4);border-radius:12px;">
        <div style="font-size:30px;font-weight:800;color:#4A6B3A;">{nb}</div>
        <div style="font-size:11px;color:#7A8C6E;text-transform:uppercase;letter-spacing:1px;">Classifications</div></div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# HERO
# ══════════════════════════════════════════════
st.markdown("""
<div style="padding:2.5rem 0 1.5rem;">
    <div class="hero-badge"><span>🤖 Deep Learning · MobileNetV2 · Grad-CAM · Chatbot Darija</span></div>
    <div class="hero-title">EcoScan AI</div>
    <div class="hero-sub">Classifiez vos déchets en un instant · Protégez la planète</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# MÉTRIQUES
# ══════════════════════════════════════════════
hq = charger_historique()
dq = pd.DataFrame(hq) if hq else pd.DataFrame()
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("📸 Analyses", len(hq))
with m2:
    if not dq.empty and "recyclable" in dq.columns:
        st.metric("♻️ Recyclables", f"{int(dq['recyclable'].sum()/len(dq)*100)}%")
    else: st.metric("♻️ Recyclables", "—")
with m3:
    if not dq.empty and "confiance" in dq.columns:
        st.metric("🎯 Confiance moy.", f"{dq['confiance'].mean():.1f}%")
    else: st.metric("🎯 Confiance moy.", "—")
with m4:
    if not dq.empty and "classe" in dq.columns:
        tc = dq["classe"].value_counts().index[0]
        st.metric("🏆 Top classe", f"{INFOS[tc]['emoji']} {tc}")
    else: st.metric("🏆 Top classe", "—")
st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Classifier", "📋 Historique", "📊 Statistiques", "📍 Points de collecte", "🤖 Chatbot",
])

# ══════════════════════════════════════════════
# TAB 1 — CLASSIFIER
# ══════════════════════════════════════════════
with tab1:
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("""<div class="sec-hdr"><div class="sec-dot"></div><div class="sec-title">Importer une image</div></div>""", unsafe_allow_html=True)
        uploaded = st.file_uploader("Glissez-déposez ou cliquez", type=["jpg","jpeg","png","webp"], label_visibility="visible")
        if uploaded:
            image = Image.open(uploaded).convert("RGB")
            st.image(image, use_container_width=True)
            w, h = image.size; kb = len(uploaded.getvalue()) / 1024
            st.markdown(f"""<div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;">
                <span style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:7px;padding:5px 12px;font-size:12px;color:#94A3B8;">📐 {w}×{h}px</span>
                <span style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:7px;padding:5px 12px;font-size:12px;color:#94A3B8;">💾 {kb:.1f} KB</span>
                <span style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:7px;padding:5px 12px;font-size:12px;color:#94A3B8;">🎨 {uploaded.type.split('/')[1].upper()}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div style="text-align:center;padding:70px 20px;color:#374151;border:1px dashed rgba(255,255,255,0.06);border-radius:18px;">
                <div style="font-size:52px;opacity:0.25;margin-bottom:14px;">📷</div>
                <div style="font-size:15px;font-weight:500;">Aucune image sélectionnée</div><div style="font-size:13px;margin-top:6px;">JPG · PNG · WEBP</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class="sec-hdr"><div class="sec-dot" style="background:#6366F1;box-shadow:0 0 7px #6366F1;"></div><div class="sec-title">Résultat IA</div></div>""", unsafe_allow_html=True)
        if uploaded:
            with st.spinner("🤖 Analyse en cours..."):
                model = charger_modele()
                img_r = image.resize((224, 224))
                img_array = np.array(img_r) / 255.0
                img_array = np.expand_dims(img_array, axis=0).astype(np.float32)
                predictions = model.predict(img_array, verbose=0)[0]
            idx = np.argmax(predictions); classe = CLASS_NAMES[idx]; confidence = predictions[idx] * 100
            info = INFOS[classe]; ajouter_entree(classe, confidence)
            rec_html = '<span class="tag-oui">✅ Recyclable</span>' if info["recyclable"] else '<span class="tag-non">❌ Non recyclable</span>'
            st.markdown(f"""<div class="result-box" style="border-color:{info['couleur']}33;">
                <span class="result-emoji">{info['emoji']}</span>
                <div class="result-class" style="color:{info['couleur']};">{classe}</div>
                <div class="confidence-badge">🎯 {confidence:.1f}%</div><br>{rec_html}
                <div class="bin-tag" style="background:{info['poubelle_color']}22;border:1px solid {info['poubelle_color']}44;color:{info['poubelle_color']};">{info['poubelle']}</div>
                </div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class="stat-row">
                <div class="stat-box"><div class="stat-val">{info['co2_kg']} kg</div><div class="stat-lbl">CO₂ économisé</div></div>
                <div class="stat-box"><div class="stat-val">{info['recyclage_rate']}%</div><div class="stat-lbl">Taux recyclage</div></div>
                <div class="stat-box"><div class="stat-val" style="font-size:14px;">{info['decomposition']}</div><div class="stat-lbl">Décomposition</div></div></div>""", unsafe_allow_html=True)
            st.markdown(f"""<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px;">
                <div class="info-card"><div class="info-card-lbl">💡 Conseil</div><div class="info-card-val">{info['conseil']}</div></div>
                <div class="info-card"><div class="info-card-lbl">📦 Exemples</div><div class="info-card-val">{info['exemples']}</div></div></div>""", unsafe_allow_html=True)
            if afficher_impact:
                st.markdown(f"""<div class="info-card"><div class="info-card-lbl">🌍 Impact</div><div class="info-card-val">{info['impact']}</div></div>""", unsafe_allow_html=True)
            if afficher_funfact:
                st.markdown(f"""<div class="funfact-box"><div style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:#6366F1;margin-bottom:6px;">⚡ Le saviez-vous ?</div>
                    <div style="font-size:14px;color:#94A3B8;font-style:italic;line-height:1.7;">{info['fun_fact']}</div></div>""", unsafe_allow_html=True)
            if afficher_top5:
                st.markdown("""<div class="sec-hdr" style="margin-top:22px;"><div class="sec-dot" style="background:#F59E0B;box-shadow:0 0 7px #F59E0B;"></div><div class="sec-title">Top 5 confiance</div></div>""", unsafe_allow_html=True)
                top5 = np.argsort(predictions)[::-1][:5]
                for rank, i in enumerate(top5):
                    pct = predictions[i]*100; nom = CLASS_NAMES[i]; inf = INFOS[nom]; is_1 = (rank==0)
                    st.markdown(f"""<div class="top5-item"><div class="top5-label">
                        <span style="display:flex;align-items:center;gap:7px;"><span>{inf['emoji']}</span>
                        <span style="color:{'#F0FDF4' if is_1 else '#64748B'};font-weight:{'600' if is_1 else '400'};">{nom}</span></span>
                        <span style="color:{'#00D68F' if is_1 else '#475569'};font-weight:{'700' if is_1 else '400'};">{pct:.1f}%</span></div>
                        <div class="bar-bg"><div class="bar-fill" style="width:{pct}%;background:{inf['couleur']};"></div></div></div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div style="text-align:center;padding:80px 20px;color:#374151;border:1px dashed rgba(255,255,255,0.06);border-radius:18px;">
                <div style="font-size:48px;opacity:0.2;margin-bottom:14px;">🤖</div>
                <div style="font-size:15px;font-weight:500;">En attente d'une image...</div></div>""", unsafe_allow_html=True)

    if uploaded and afficher_gradcam:
        st.divider()
        st.markdown("""<div class="sec-hdr"><div class="sec-dot" style="background:#F43F5E;box-shadow:0 0 7px #F43F5E;"></div><div class="sec-title">🔥 Grad-CAM — Zones d'attention du modèle</div></div>""", unsafe_allow_html=True)
        with st.spinner("🧠 Génération Grad-CAM..."):
            heatmap = generer_gradcam(model, img_array, idx)
        if heatmap is not None:
            gradcam_image = superposer_gradcam(image, heatmap)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown('<p style="text-align:center;color:#475569;font-size:12px;text-transform:uppercase;letter-spacing:1px;">Originale</p>', unsafe_allow_html=True)
                st.image(image.resize((224,224)), use_container_width=True)
            with c2:
                st.markdown('<p style="text-align:center;color:#475569;font-size:12px;text-transform:uppercase;letter-spacing:1px;">Carte thermique</p>', unsafe_allow_html=True)
                fig, ax = plt.subplots(figsize=(3,3)); fig.patch.set_facecolor('#0D1117'); ax.set_facecolor('#0D1117')
                ax.imshow(cv2.resize(heatmap,(224,224)), cmap="jet"); ax.axis("off"); st.pyplot(fig, use_container_width=True); plt.close()
            with c3:
                st.markdown('<p style="text-align:center;color:#475569;font-size:12px;text-transform:uppercase;letter-spacing:1px;">Superposition</p>', unsafe_allow_html=True)
                st.image(gradcam_image, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 2 — HISTORIQUE
# ══════════════════════════════════════════════
with tab2:
    st.markdown("""<div class="sec-hdr"><div class="sec-dot" style="background:#3B82F6;box-shadow:0 0 7px #3B82F6;"></div><div class="sec-title">Historique des Classifications</div></div>""", unsafe_allow_html=True)
    history = charger_historique()
    if len(history) == 0:
        st.info("Aucun historique disponible.")
    else:
        df = pd.DataFrame(history)
        h1,h2,h3,h4 = st.columns(4)
        with h1: st.metric("Total", len(df))
        with h2: last_c = df.iloc[-1]["classe"]; st.metric("Dernière", f"{INFOS[last_c]['emoji']} {last_c}")
        with h3: recyc = int(df["recyclable"].sum()) if "recyclable" in df.columns else 0; st.metric("Recyclables", f"{recyc}/{len(df)}")
        with h4: best = df["confiance"].max() if "confiance" in df.columns else 0; st.metric("Meilleure conf.", f"{best:.1f}%")
        st.markdown("<br>", unsafe_allow_html=True)
        cols_voulues = ["timestamp","emoji","classe","confiance","recyclable","poubelle"]
        cols_ok = [c for c in cols_voulues if c in df.columns]
        df_disp = df[cols_ok].copy()
        noms = {"timestamp":"📅 Date","emoji":"🏷️","classe":"Classe","confiance":"Confiance (%)","recyclable":"♻️ Recyclable","poubelle":"🗑️ Poubelle"}
        df_disp.columns = [noms[c] for c in cols_ok]
        st.dataframe(df_disp, use_container_width=True, hide_index=True)
        b1,b2 = st.columns(2)
        with b1:
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Télécharger CSV", csv, "history.csv", "text/csv", use_container_width=True)
        with b2:
            if st.button("🗑️ Supprimer historique", use_container_width=True):
                sauvegarder_historique([]); st.rerun()

# ══════════════════════════════════════════════
# TAB 3 — STATISTIQUES
# ══════════════════════════════════════════════
with tab3:
    st.markdown("""<div class="sec-hdr"><div class="sec-dot" style="background:#F59E0B;box-shadow:0 0 7px #F59E0B;"></div><div class="sec-title">Statistiques</div></div>""", unsafe_allow_html=True)
    history = charger_historique()
    if len(history) < 2:
        st.warning("Pas assez de données.")
    else:
        df = pd.DataFrame(history)
        PC = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8"), margin=dict(t=50,b=20,l=20,r=20))
        GC = "rgba(255,255,255,0.05)"
        ca,cb = st.columns(2)
        with ca:
            counts = df["classe"].value_counts(); colors = [INFOS[c]["couleur"] for c in counts.index]
            fig1 = go.Figure(go.Pie(labels=[f"{INFOS[c]['emoji']} {c}" for c in counts.index], values=counts.values, hole=0.55, marker_colors=colors, textinfo="label+percent", textfont_size=12))
            fig1.update_layout(**PC, title=dict(text="Distribution par catégorie",font=dict(color="#94A3B8",size=15)), showlegend=False, annotations=[dict(text=f"<b>{len(df)}</b><br>analyses",x=0.5,y=0.5,font_size=13,font_color="#00D68F",showarrow=False)])
            st.plotly_chart(fig1, use_container_width=True)
        with cb:
            conf = df.groupby("classe")["confiance"].mean().reset_index(); fig2 = go.Figure()
            for _,r in conf.iterrows():
                fig2.add_trace(go.Bar(x=[f"{INFOS[r['classe']]['emoji']} {r['classe']}"],y=[r["confiance"]],marker_color=INFOS[r["classe"]]["couleur"],marker_opacity=0.85,showlegend=False))
            fig2.add_hline(y=df["confiance"].mean(),line_dash="dash",line_color="#00D68F",line_width=1.5)
            fig2.update_layout(**PC, title=dict(text="Confiance moyenne par classe",font=dict(color="#94A3B8",size=15)), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True,gridcolor=GC,range=[0,105]), bargap=0.35)
            st.plotly_chart(fig2, use_container_width=True)
        cc,cd = st.columns(2)
        with cc:
            df2 = df.copy(); df2["n"] = range(len(df2)); fig3 = go.Figure()
            for c in CLASS_NAMES:
                sub = df2[df2["classe"]==c]
                if not sub.empty:
                    fig3.add_trace(go.Scatter(x=sub["n"],y=sub["confiance"],mode="markers",name=f"{INFOS[c]['emoji']} {c}",marker=dict(color=INFOS[c]["couleur"],size=10,opacity=0.85)))
            fig3.update_layout(**PC, title=dict(text="Évolution des classifications",font=dict(color="#94A3B8",size=15)), xaxis=dict(showgrid=False,title="N° analyse"), yaxis=dict(showgrid=True,gridcolor=GC,title="Confiance (%)",range=[0,105]), legend=dict(font=dict(color="#94A3B8",size=11),bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig3, use_container_width=True)
        with cd:
            ry = int(df["recyclable"].sum()) if "recyclable" in df.columns else 0; rn = len(df)-ry
            fig4 = go.Figure(go.Bar(x=["Recyclable","Non recyclable"],y=[ry,rn],marker_color=["#00D68F","#F43F5E"],marker_opacity=0.85,text=[ry,rn],textposition="outside",textfont=dict(color="#94A3B8")))
            fig4.update_layout(**PC, title=dict(text="Recyclable vs Non recyclable",font=dict(color="#94A3B8",size=15)), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True,gridcolor=GC), bargap=0.4, showlegend=False)
            st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 4 — POINTS DE COLLECTE
# ══════════════════════════════════════════════
with tab4:
    st.markdown("""<div class="sec-hdr"><div class="sec-dot" style="background:#F59E0B;box-shadow:0 0 7px #F59E0B;"></div><div class="sec-title">📍 Trouver un point de collecte près de chez vous</div></div>""", unsafe_allow_html=True)
    col_form1, col_form2 = st.columns([3, 1])
    with col_form1:
        adresse_input = st.text_input("📍 Votre adresse", placeholder="Ex : 15 Rue de la République, Paris", label_visibility="collapsed")
    with col_form2:
        pays_code = st.selectbox("Pays", options=list(COUNTRIES.keys()), format_func=lambda x: COUNTRIES[x], label_visibility="collapsed")
    col_opt1, col_opt2, col_opt3 = st.columns([1, 1, 2])
    with col_opt1:
        rayon_km = st.selectbox("📏 Rayon", options=[1,2,3,5,10,15,20], format_func=lambda x: f"{x} km", index=3, label_visibility="collapsed")
    with col_opt2:
        hist = charger_historique(); dernier_type = hist[-1]["classe"] if hist else None
        idx_default = 0
        type_options = [" Tous les types"] + [f" {INFOS[c]['emoji']} {c.capitalize()}" for c in CLASS_NAMES]
        if dernier_type: idx_default = CLASS_NAMES.index(dernier_type) + 1
        filtre_select = st.selectbox("♻️ Filtrer par déchet", options=type_options, index=idx_default, label_visibility="collapsed")
        filtre_type = filtre_select.strip().split(" ")[-1].lower()
        if filtre_type == "tous": filtre_type = None
    with col_opt3:
        st.markdown("<br>", unsafe_allow_html=True)
        rechercher = st.button("🔍 Rechercher les points de collecte", use_container_width=True, type="primary")
    if rechercher:
        if not adresse_input.strip():
            st.error("❌ Veuillez entrer une adresse.")
        else:
            with st.spinner("📍 Géocodage de l'adresse..."):
                geo = geocoder_adresse(adresse_input, pays_code)
            if geo is None:
                st.error("❌ Adresse introuvable.")
            else:
                user_lat, user_lon, display_name = geo
                st.success(f"✅ Position trouvée : *{display_name}*")
                with st.spinner("♻️ Recherche des points de collecte via OpenStreetMap..."):
                    centres = trouver_centres(user_lat, user_lon, rayon_km, filtre_type)
                if not centres:
                    st.warning(f"😔 Aucun point de recyclage trouvé dans un rayon de {rayon_km} km.")
                else:
                    rm1,rm2,rm3,rm4 = st.columns(4)
                    with rm1: st.metric("♻️ Points trouvés", len(centres))
                    with rm2: st.metric("🏭 Déchèteries", sum(1 for c in centres if c["is_decheterie"]))
                    with rm3: st.metric("📏 Plus proche", f"{centres[0]['distance']} km")
                    with rm4: st.metric("🚶 À pied", f"{centres[0]['walking_min']} min")
                    st.markdown("<br>", unsafe_allow_html=True)
                    if afficher_carte:
                        carte_html = generer_carte_html(user_lat, user_lon, centres)
                        components.html(carte_html, height=500, scrolling=False)
                    st.divider()
                    st.subheader("♻️ Liste des points de collecte")

                    for c in centres:
                        icon = "🏭" if c["is_decheterie"] else "♻️"
                        badge = "🔴 Déchèterie" if c["is_decheterie"] else "🟢 Point de recyclage"
                        gmaps_url = f"https://www.google.com/maps/dir/?api=1&destination={c['lat']},{c['lon']}"
                        osm_url = f"https://www.openstreetmap.org/?mlat={c['lat']}&mlon={c['lon']}#map=17/{c['lat']}/{c['lon']}"

                        with st.container(border=True):
                            # Ligne titre + badge
                            col_titre, col_badge = st.columns([3, 1])
                            with col_titre:
                                st.markdown(f"### {icon} {c['nom']}")
                            with col_badge:
                                st.markdown(f"<div style='padding:6px 0;font-size:13px;font-weight:600;'>{badge}</div>", unsafe_allow_html=True)

                            # Adresse + distance
                            col_addr, col_dist = st.columns([3, 1])
                            with col_addr:
                                st.markdown(f"📍 **Adresse :** {c['adresse']}")
                                st.markdown(f"🏷️ **Type :** {c['type']}")
                                if c["types_acceptes"]:
                                    st.markdown("**Accepte :** " + " · ".join(c["types_acceptes"][:8]))
                            with col_dist:
                                st.metric("Distance", f"{c['distance']} km")
                                st.caption(f"🚶 {c['walking_min']} min · 🚗 {c['driving_min']} min")

                            # Boutons liens
                            col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 3])
                            with col_btn1:
                                st.link_button("🗺️ Itinéraire Google Maps", gmaps_url, use_container_width=True)
                            with col_btn2:
                                st.link_button("📍 Voir sur OpenStreetMap", osm_url, use_container_width=True)
                            with col_btn3:
                                st.caption(f"📌 Coordonnées : {c['lat']:.5f}, {c['lon']:.5f}")
    else:
        st.info("📍 Entrez votre adresse ci-dessus et cliquez sur **Rechercher** pour trouver les points de collecte proches (données réelles OpenStreetMap).")
        with st.expander("💡 Exemples d'adresses à essayer"):
            st.markdown("""
- 🇲🇦 `Jamaa el Fna, Marrakech` · `Hay Riad, Rabat` · `Médina, Fès`
- 🇫🇷 `Place de la Concorde, Paris` · `Belleville, Lyon`
- 🇧🇪 `Grand Place, Bruxelles`
            """)

# ══════════════════════════════════════════════
# TAB 5 — CHATBOT  ← CORRIGÉ
# ══════════════════════════════════════════════
with tab5:

    # Initialiser session_state
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "chat_input_prefill" not in st.session_state:
        st.session_state.chat_input_prefill = ""

    # ── Traiter un clic sur suggestion (set depuis session_state) ──
    if st.session_state.chat_input_prefill:
        question_auto = st.session_state.chat_input_prefill
        st.session_state.chat_input_prefill = ""
        st.session_state.chat_messages.append({"role": "user", "content": question_auto})
        reponse, score = trouver_reponse_chatbot(question_auto)
        if reponse is None:
            reponse = generer_reponse_defaut(question_auto)
        st.session_state.chat_messages.append({"role": "assistant", "content": reponse})

    # ── Écran d'accueil si pas de messages ──
    if len(st.session_state.chat_messages) == 0:
        st.markdown("""
        <div class="chat-welcome-box">
            <div style="font-size:52px;margin-bottom:12px;">🤖</div>
            <div style="font-family:'Syne',sans-serif;font-size:26px;font-weight:800;color:#F0FDF4;margin-bottom:8px;">EcoBot</div>
            <div style="font-size:15px;color:#64748B;line-height:1.7;">
                Votre assistant écologique — posez vos questions sur le recyclage<br>
                en <b style="color:#CBD5E1;">français</b> ou en <b style="color:#CBD5E1;">داريجة</b> 🇲🇦
            </div>
            <div style="display:flex;gap:8px;justify-content:center;margin-top:14px;flex-wrap:wrap;">
                <span style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:50px;padding:5px 14px;font-size:12px;color:#000000;">🇫🇷 Français</span>
                <span style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:50px;padding:5px 14px;font-size:12px;color:#94A3B8;">🇲🇦 الدارجة</span>
                <span style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:50px;padding:5px 14px;font-size:12px;color:#94A3B8;">🌍 18+ sujets</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Suggestions avec vrais boutons Streamlit ──
        st.markdown("**💡 Questions fréquentes — cliquez pour envoyer :**")
        col_fr, col_ar = st.columns(2)

        with col_fr:
            st.markdown("<p style='font-size:12px;color:#000000;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;'>🇫🇷 En français</p>", unsafe_allow_html=True)
            for emoji, texte in SUGGESTIONS_FR:
                if st.button(f"{emoji} {texte}", key=f"sug_fr_{texte}", use_container_width=True):
                    st.session_state.chat_input_prefill = texte
                    st.rerun()

        with col_ar:
            st.markdown("<p style='font-size:12px;color:#475569;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;'>🇲🇦 بالدارجة</p>", unsafe_allow_html=True)
            for emoji, texte in SUGGESTIONS_DARIJA:
                if st.button(f"{emoji} {texte}", key=f"sug_ar_{texte}", use_container_width=True):
                    st.session_state.chat_input_prefill = texte
                    st.rerun()

    # ── Afficher les messages existants ──
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── Input du chat ──
    question = st.chat_input("💬 Posez votre question sur le recyclage... (français ou داريجة)")

    if question:
        st.session_state.chat_messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        reponse, score = trouver_reponse_chatbot(question)
        if reponse is None:
            reponse = generer_reponse_defaut(question)
        st.session_state.chat_messages.append({"role": "assistant", "content": reponse})
        with st.chat_message("assistant"):
            st.markdown(reponse)

    # ── Bouton effacer ──
    if st.session_state.chat_messages:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Effacer la conversation", use_container_width=True, key="clear_chat"):
            st.session_state.chat_messages = []
            st.rerun()

# ══════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════
st.divider()
st.markdown("""
<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;flex-wrap:wrap;gap:10px;">
    <div style="font-size:13px;color:#7A8C6E;"><b style="color:#4A6B3A;">EcoScan AI</b> · Deep Learning · MobileNetV2 · Chatbot Darija · 2026</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
        <span style="font-size:12px;color:#5A7A4A;background:rgba(156,175,136,0.15);border:1px solid rgba(156,175,136,0.35);padding:4px 12px;border-radius:20px;">♻️ Recyclage Intelligent</span>
        <span style="font-size:12px;color:#5A7A4A;background:rgba(156,175,136,0.15);border:1px solid rgba(156,175,136,0.35);padding:4px 12px;border-radius:20px;">🌍 Impact Environnemental</span>
        <span style="font-size:12px;color:#5A7A4A;background:rgba(156,175,136,0.15);border:1px solid rgba(156,175,136,0.35);padding:4px 12px;border-radius:20px;">🤖 Chatbot Darija</span>
    </div>
</div>
""", unsafe_allow_html=True)