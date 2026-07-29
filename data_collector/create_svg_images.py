import os
from pathlib import Path

IMAGES_DIR = Path(__file__).resolve().parent / "images"
IMAGES_DIR.mkdir(exist_ok=True)

# SVG templates for 35 words
svgs = {
    "01_Paani.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#38bdf8;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#0284c7;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="20" fill="#e0f2fe"/>
  <!-- Glass of Water -->
  <path d="M60 50 L70 160 C70 170 130 170 130 160 L140 50 Z" fill="url(#grad1)" opacity="0.8"/>
  <path d="M55 45 Q100 35 145 45 Q100 55 55 45" fill="#bae6fd" stroke="#0284c7" stroke-width="3"/>
  <path d="M65 80 Q100 90 135 80 Q100 70 65 80" fill="#38bdf8" opacity="0.6"/>
  <!-- Water Drops -->
  <path d="M100 15 Q110 30 100 38 Q90 30 100 15 Z" fill="#0284c7"/>
</svg>''',

    "02_Billi.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#fef3c7"/>
  <!-- Cat Head -->
  <circle cx="100" cy="110" r="50" fill="#f59e0b"/>
  <!-- Ears -->
  <polygon points="65,75 50,30 85,65" fill="#d97706"/>
  <polygon points="135,75 150,30 115,65" fill="#d97706"/>
  <!-- Inner Ears -->
  <polygon points="67,70 57,38 80,63" fill="#fbcfe8"/>
  <polygon points="133,70 143,38 120,63" fill="#fbcfe8"/>
  <!-- Eyes -->
  <ellipse cx="80" cy="105" rx="8" ry="12" fill="#15803d"/>
  <ellipse cx="120" cy="105" rx="8" ry="12" fill="#15803d"/>
  <circle cx="80" cy="105" r="3" fill="#ffffff"/>
  <circle cx="120" cy="105" r="3" fill="#ffffff"/>
  <!-- Nose & Mouth -->
  <polygon points="95,120 105,120 100,126" fill="#f43f5e"/>
  <path d="M92 128 Q100 135 100 128 Q100 135 108 128" fill="none" stroke="#78350f" stroke-width="3" stroke-linecap="round"/>
  <!-- Whiskers -->
  <line x1="45" y1="115" x2="70" y2="118" stroke="#78350f" stroke-width="2"/>
  <line x1="45" y1="125" x2="70" y2="123" stroke="#78350f" stroke-width="2"/>
  <line x1="155" y1="115" x2="130" y2="118" stroke="#78350f" stroke-width="2"/>
  <line x1="155" y1="125" x2="130" y2="123" stroke="#78350f" stroke-width="2"/>
</svg>''',

    "03_Kutta.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#ffedd5"/>
  <!-- Dog Face -->
  <circle cx="100" cy="110" r="55" fill="#b45309"/>
  <!-- Floppy Ears -->
  <ellipse cx="45" cy="110" rx="18" ry="35" fill="#78350f"/>
  <ellipse cx="155" cy="110" rx="18" ry="35" fill="#78350f"/>
  <!-- Snout -->
  <ellipse cx="100" cy="125" rx="25" ry="20" fill="#fde68a"/>
  <!-- Nose -->
  <ellipse cx="100" cy="115" rx="10" ry="7" fill="#1c1917"/>
  <!-- Eyes -->
  <circle cx="80" cy="95" r="7" fill="#1c1917"/>
  <circle cx="120" cy="95" r="7" fill="#1c1917"/>
  <circle cx="82" cy="93" r="2" fill="#ffffff"/>
  <circle cx="122" cy="93" r="2" fill="#ffffff"/>
  <!-- Tongue -->
  <path d="M95 133 Q100 155 105 133 Z" fill="#f43f5e"/>
</svg>''',

    "04_Ghar.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#ecfdf5"/>
  <!-- Roof -->
  <polygon points="100,30 20,90 180,90" fill="#dc2626"/>
  <!-- Walls -->
  <rect x="40" y="90" width="120" height="85" fill="#fef08a" stroke="#ca8a04" stroke-width="2"/>
  <!-- Door -->
  <rect x="85" y="125" width="30" height="50" rx="4" fill="#854d0e"/>
  <circle cx="108" cy="150" r="3" fill="#fef08a"/>
  <!-- Windows -->
  <rect x="55" y="105" width="22" height="22" rx="3" fill="#38bdf8" stroke="#0284c7" stroke-width="2"/>
  <rect x="123" y="105" width="22" height="22" rx="3" fill="#38bdf8" stroke="#0284c7" stroke-width="2"/>
</svg>''',

    "05_Khara.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#f0fdf4"/>
  <!-- Standing Person Silhouette / Character -->
  <circle cx="100" cy="50" r="22" fill="#475569"/>
  <!-- Body -->
  <path d="M75 80 L125 80 L118 135 L82 135 Z" fill="#2563eb"/>
  <!-- Legs -->
  <rect x="84" y="135" width="12" height="50" rx="4" fill="#334155"/>
  <rect x="104" y="135" width="12" height="50" rx="4" fill="#334155"/>
  <!-- Arms standing tall -->
  <rect x="62" y="80" width="10" height="45" rx="4" fill="#475569"/>
  <rect x="128" y="80" width="10" height="45" rx="4" fill="#475569"/>
  <!-- Arrow UP showing Standing stance -->
  <path d="M100 175 L100 160 M95 165 L100 160 L105 165" stroke="#16a34a" stroke-width="3" stroke-linecap="round"/>
</svg>''',

    "06_Bara.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#f3e8ff"/>
  <!-- Big Object vs Small Object -->
  <rect x="35" y="45" width="110" height="110" rx="15" fill="#9333ea"/>
  <text x="90" y="112" font-family="Arial" font-size="28" font-weight="bold" fill="#ffffff" text-anchor="middle">BIG</text>
  <rect x="155" y="125" width="30" height="30" rx="5" fill="#c084fc"/>
  <text x="170" y="144" font-family="Arial" font-size="10" fill="#ffffff" text-anchor="middle">small</text>
</svg>''',

    "07_Larka.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#e0f2fe"/>
  <!-- Boy Face -->
  <circle cx="100" cy="95" r="45" fill="#fde047"/>
  <!-- Hair -->
  <path d="M55 85 C65 50 135 50 145 85 C130 65 70 65 55 85 Z" fill="#1e293b"/>
  <!-- Eyes -->
  <circle cx="82" cy="95" r="6" fill="#0f172a"/>
  <circle cx="118" cy="95" r="6" fill="#0f172a"/>
  <!-- Smile -->
  <path d="M85 118 Q100 132 115 118" fill="none" stroke="#0f172a" stroke-width="4" stroke-linecap="round"/>
  <!-- Shirt -->
  <path d="M60 145 Q100 135 140 145 L150 190 L50 190 Z" fill="#0284c7"/>
</svg>''',

    "08_Larki.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#fce7f3"/>
  <!-- Girl Hair Back -->
  <ellipse cx="100" cy="110" rx="58" ry="50" fill="#701a75"/>
  <!-- Face -->
  <circle cx="100" cy="95" r="42" fill="#fde047"/>
  <!-- Bangs -->
  <path d="M58 85 Q100 65 142 85 Q100 75 58 85 Z" fill="#701a75"/>
  <!-- Pigtails / Bows -->
  <circle cx="48" cy="70" r="14" fill="#ec4899"/>
  <circle cx="152" cy="70" r="14" fill="#ec4899"/>
  <!-- Eyes -->
  <circle cx="83" cy="95" r="5" fill="#0f172a"/>
  <circle cx="117" cy="95" r="5" fill="#0f172a"/>
  <!-- Smile -->
  <path d="M86 115 Q100 128 114 115" fill="none" stroke="#0f172a" stroke-width="3" stroke-linecap="round"/>
  <!-- Dress -->
  <path d="M65 140 Q100 132 135 140 L150 190 L50 190 Z" fill="#db2777"/>
</svg>''',

    "09_Doodh.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#f1f5f9"/>
  <!-- Milk Bottle / Glass -->
  <rect x="65" y="45" width="70" height="120" rx="12" fill="#ffffff" stroke="#cbd5e1" stroke-width="4"/>
  <rect x="75" y="30" width="50" height="18" rx="4" fill="#38bdf8"/>
  <rect x="70" y="80" width="60" height="75" rx="6" fill="#f8fafc"/>
  <text x="100" y="125" font-family="Arial" font-size="18" font-weight="bold" fill="#0284c7" text-anchor="middle">MILK</text>
  <!-- Splash -->
  <circle cx="145" cy="55" r="6" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>
  <circle cx="155" cy="70" r="4" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>
</svg>''',

    "10_Phool.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#fff7ed"/>
  <!-- Stem & Leaf -->
  <path d="M100 110 Q90 150 100 185" fill="none" stroke="#16a34a" stroke-width="6"/>
  <path d="M97 145 Q70 140 75 160 Q95 160 97 145 Z" fill="#22c55e"/>
  <!-- Petals -->
  <circle cx="100" cy="65" r="22" fill="#f43f5e"/>
  <circle cx="130" cy="85" r="22" fill="#f43f5e"/>
  <circle cx="120" cy="120" r="22" fill="#f43f5e"/>
  <circle cx="80" cy="120" r="22" fill="#f43f5e"/>
  <circle cx="70" cy="85" r="22" fill="#f43f5e"/>
  <!-- Center -->
  <circle cx="100" cy="92" r="20" fill="#facc15"/>
</svg>''',

    "11_Machhli.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#e0f2fe"/>
  <!-- Fish Body -->
  <path d="M160 100 Q90 40 40 100 Q90 160 160 100 Z" fill="#f97316"/>
  <!-- Tail -->
  <polygon points="150,100 185,65 185,135" fill="#ea580c"/>
  <!-- Fin -->
  <polygon points="90,70 115,45 110,75" fill="#ea580c"/>
  <!-- Eye -->
  <circle cx="65" cy="90" r="6" fill="#ffffff"/>
  <circle cx="63" cy="90" r="3" fill="#000000"/>
  <!-- Bubbles -->
  <circle cx="30" cy="80" r="5" fill="none" stroke="#38bdf8" stroke-width="2"/>
  <circle cx="20" cy="60" r="8" fill="none" stroke="#38bdf8" stroke-width="2"/>
</svg>''',

    "12_Chiriya.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#f0fdf4"/>
  <!-- Bird Body -->
  <circle cx="95" cy="105" r="40" fill="#06b6d4"/>
  <!-- Bird Head -->
  <circle cx="130" cy="80" r="26" fill="#0891b2"/>
  <!-- Wing -->
  <path d="M70 105 Q100 130 65 135 Z" fill="#155e75"/>
  <!-- Beak -->
  <polygon points="154,78 178,85 154,92" fill="#f59e0b"/>
  <!-- Eye -->
  <circle cx="138" cy="75" r="4" fill="#ffffff"/>
  <circle cx="139" cy="75" r="2" fill="#000000"/>
  <!-- Tail -->
  <polygon points="60,110 30,120 40,100" fill="#155e75"/>
</svg>''',

    "13_Gaon.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#fef9c3"/>
  <!-- Green Hills -->
  <path d="M0 140 Q60 90 130 140 Q170 110 200 150 L200 200 L0 200 Z" fill="#4ade80"/>
  <!-- Small Hut 1 -->
  <polygon points="40,110 70,110 55,90" fill="#b45309"/>
  <rect x="43" y="110" width="24" height="20" fill="#fde047"/>
  <!-- Small Hut 2 -->
  <polygon points="120,125 160,125 140,100" fill="#b45309"/>
  <rect x="125" y="125" width="30" height="25" fill="#fde047"/>
  <!-- Sun -->
  <circle cx="165" cy="45" r="22" fill="#facc15"/>
</svg>''',

    "14_Kahan.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#f8fafc"/>
  <!-- Map Pin / Location Question -->
  <path d="M100 35 C70 35 50 58 50 88 C50 130 100 175 100 175 C100 175 150 130 150 88 C150 58 130 35 100 35 Z" fill="#ef4444"/>
  <circle cx="100" cy="82" r="22" fill="#ffffff"/>
  <text x="100" y="93" font-family="Arial" font-size="32" font-weight="bold" fill="#ef4444" text-anchor="middle">?</text>
</svg>''',

    "15_Main.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#fae8ff"/>
  <!-- Person pointing to self "I / Me" -->
  <circle cx="100" cy="70" r="30" fill="#6366f1"/>
  <path d="M55 165 C55 120 145 120 145 165 Z" fill="#4f46e5"/>
  <!-- Hand pointing towards chest -->
  <circle cx="100" cy="135" r="10" fill="#fde047"/>
  <text x="100" y="185" font-family="Arial" font-size="18" font-weight="bold" fill="#4338ca" text-anchor="middle">I / ME</text>
</svg>''',

    "16_Tamatar.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#fef2f2"/>
  <!-- Tomato Body -->
  <circle cx="100" cy="115" r="55" fill="#dc2626"/>
  <!-- Highlight -->
  <ellipse cx="80" cy="95" rx="14" ry="8" fill="#ef4444"/>
  <!-- Leaf Crown -->
  <polygon points="100,50 90,65 75,55 88,72 65,75 88,82 100,68 112,82 135,75 112,72 125,55 110,65" fill="#16a34a"/>
  <path d="M100 42 L100 58" stroke="#15803d" stroke-width="4" stroke-linecap="round"/>
</svg>''',

    "17_Dabba.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#fffbe6"/>
  <!-- 3D Gift Box -->
  <rect x="50" y="80" width="100" height="85" rx="6" fill="#d97706"/>
  <rect x="42" y="65" width="116" height="22" rx="4" fill="#b45309"/>
  <!-- Ribbon Vertical -->
  <rect x="90" y="65" width="20" height="100" fill="#dc2626"/>
  <!-- Bow -->
  <circle cx="82" cy="50" r="16" fill="#dc2626"/>
  <circle cx="118" cy="50" r="16" fill="#dc2626"/>
  <circle cx="100" cy="53" r="8" fill="#991b1b"/>
</svg>''',

    "18_Thanda.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#e0f2fe"/>
  <!-- Ice Cubes -->
  <rect x="45" y="75" width="65" height="65" rx="10" fill="#7dd3fc" stroke="#0284c7" stroke-width="3" opacity="0.9"/>
  <rect x="90" y="50" width="65" height="65" rx="10" fill="#bae6fd" stroke="#0284c7" stroke-width="3" opacity="0.8"/>
  <!-- Snowflake Icon -->
  <path d="M100 20 L100 40 M100 30 L90 25 M100 30 L110 25" stroke="#0284c7" stroke-width="3" stroke-linecap="round"/>
  <text x="100" y="175" font-family="Arial" font-size="18" font-weight="bold" fill="#0369a1" text-anchor="middle">COLD / ICE</text>
</svg>''',

    "19_Dhool.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#fef3c7"/>
  <!-- Drum (Dhol) Body -->
  <ellipse cx="100" cy="100" rx="70" ry="40" fill="#b45309"/>
  <rect x="30" y="70" width="140" height="60" fill="#d97706"/>
  <ellipse cx="30" cy="100" rx="15" ry="30" fill="#78350f"/>
  <ellipse cx="170" cy="100" rx="15" ry="30" fill="#f59e0b"/>
  <!-- Drum Sticks -->
  <line x1="45" y1="50" x2="80" y2="85" stroke="#451a03" stroke-width="6" stroke-linecap="round"/>
  <line x1="155" y1="50" x2="120" y2="85" stroke="#451a03" stroke-width="6" stroke-linecap="round"/>
</svg>''',

    "20_Qalam.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#f8fafc"/>
  <!-- Fountain Pen -->
  <g transform="rotate(-35 100 100)">
    <rect x="90" y="30" width="20" height="100" fill="#1e293b"/>
    <polygon points="90,130 110,130 100,165" fill="#f59e0b"/>
    <polygon points="96,165 104,165 100,178" fill="#0f172a"/>
    <rect x="87" y="60" width="26" height="8" rx="2" fill="#f59e0b"/>
  </g>
</svg>''',

    "21_Khargoosh.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#f0fdf4"/>
  <!-- Long Ears -->
  <ellipse cx="80" cy="55" rx="12" ry="40" fill="#ffffff" stroke="#cbd5e1" stroke-width="3"/>
  <ellipse cx="120" cy="55" rx="12" ry="40" fill="#ffffff" stroke="#cbd5e1" stroke-width="3"/>
  <ellipse cx="80" cy="55" rx="6" ry="28" fill="#fbcfe8"/>
  <ellipse cx="120" cy="55" rx="6" ry="28" fill="#fbcfe8"/>
  <!-- Head -->
  <circle cx="100" cy="115" r="45" fill="#ffffff" stroke="#cbd5e1" stroke-width="3"/>
  <!-- Eyes -->
  <circle cx="83" cy="105" r="5" fill="#0f172a"/>
  <circle cx="117" cy="105" r="5" fill="#0f172a"/>
  <!-- Pink Nose -->
  <polygon points="95,118 105,118 100,124" fill="#f43f5e"/>
  <!-- Cheeks -->
  <circle cx="70" cy="122" r="8" fill="#fbcfe8" opacity="0.6"/>
  <circle cx="130" cy="122" r="8" fill="#fbcfe8" opacity="0.6"/>
</svg>''',

    "22_Ghubara.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#fef2f2"/>
  <!-- Red Balloon -->
  <ellipse cx="100" cy="85" rx="45" ry="55" fill="#ef4444"/>
  <ellipse cx="80" cy="65" rx="12" ry="18" fill="#fca5a5" opacity="0.6"/>
  <polygon points="95,140 105,140 100,147" fill="#dc2626"/>
  <!-- String -->
  <path d="M100 147 Q110 165 95 185" fill="none" stroke="#78350f" stroke-width="3" stroke-linecap="round"/>
</svg>''',

    "23_Jhoola.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#ecfdf5"/>
  <!-- Swing Frame -->
  <line x1="40" y1="30" x2="160" y2="30" stroke="#475569" stroke-width="6"/>
  <line x1="50" y1="30" x2="30" y2="180" stroke="#475569" stroke-width="5"/>
  <line x1="150" y1="30" x2="170" y2="180" stroke="#475569" stroke-width="5"/>
  <!-- Ropes -->
  <line x1="80" y1="30" x2="80" y2="130" stroke="#ca8a04" stroke-width="3"/>
  <line x1="120" y1="30" x2="120" y2="130" stroke="#ca8a04" stroke-width="3"/>
  <!-- Wooden Seat -->
  <rect x="70" y="130" width="60" height="12" rx="3" fill="#854d0e"/>
</svg>''',

    "24_Joota.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#eff6ff"/>
  <!-- Sneaker Shoe -->
  <path d="M35 120 L55 80 Q90 85 110 105 L165 110 C175 110 180 135 165 145 L35 145 Z" fill="#2563eb"/>
  <rect x="30" y="145" width="145" height="18" rx="4" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>
  <!-- Laces -->
  <line x1="75" y1="95" x2="90" y2="105" stroke="#ffffff" stroke-width="3"/>
  <line x1="82" y1="105" x2="97" y2="115" stroke="#ffffff" stroke-width="3"/>
</svg>''',

    "25_Seeb.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#fef2f2"/>
  <!-- Apple Body -->
  <path d="M100 60 C120 40 160 55 155 95 C150 135 115 165 100 165 C85 165 50 135 45 95 C40 55 80 40 100 60 Z" fill="#dc2626"/>
  <!-- Stem -->
  <path d="M100 60 Q105 35 115 30" fill="none" stroke="#78350f" stroke-width="4" stroke-linecap="round"/>
  <!-- Leaf -->
  <path d="M105 45 Q125 35 130 50 Q110 55 105 45 Z" fill="#16a34a"/>
</svg>''',

    "26_Zaban.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#fff1f2"/>
  <!-- Mouth Outline -->
  <path d="M40 90 Q100 40 160 90 Q100 130 40 90 Z" fill="#9f1239"/>
  <!-- Tongue sticking out -->
  <path d="M70 100 Q100 175 130 100 Z" fill="#fb7185" stroke="#e11d48" stroke-width="3"/>
  <line x1="100" y1="110" x2="100" y2="145" stroke="#e11d48" stroke-width="3"/>
</svg>''',

    "27_Shaam.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#0f172a"/>
  <!-- Sunset Sky -->
  <path d="M0 100 Q100 60 200 100 L200 200 L0 200 Z" fill="#ea580c"/>
  <circle cx="100" cy="100" r="35" fill="#facc15"/>
  <!-- Mountains -->
  <polygon points="0,150 60,110 120,160" fill="#451a03"/>
  <polygon points="80,160 140,120 200,165" fill="#451a03"/>
  <text x="100" y="45" font-family="Arial" font-size="18" font-weight="bold" fill="#fde047" text-anchor="middle">EVENING</text>
</svg>''',

    "28_Haathi.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#f1f5f9"/>
  <!-- Elephant Body -->
  <circle cx="110" cy="115" r="50" fill="#64748b"/>
  <!-- Head -->
  <circle cx="65" cy="100" r="35" fill="#64748b"/>
  <!-- Ear -->
  <ellipse cx="80" cy="90" rx="22" ry="30" fill="#94a3b8"/>
  <!-- Trunk -->
  <path d="M45 110 Q20 120 25 145 Q35 155 40 140 Q35 125 55 120 Z" fill="#475569"/>
  <!-- Eye -->
  <circle cx="55" cy="90" r="4" fill="#ffffff"/>
  <circle cx="54" cy="90" r="2" fill="#000000"/>
  <!-- Tusk -->
  <path d="M48 118 Q35 128 42 130 Z" fill="#ffffff"/>
</svg>''',

    "29_Makkhi.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#f8fafc"/>
  <!-- Wings -->
  <ellipse cx="80" cy="75" rx="18" ry="35" fill="#bae6fd" opacity="0.7" transform="rotate(-30 80 75)"/>
  <ellipse cx="120" cy="75" rx="18" ry="35" fill="#bae6fd" opacity="0.7" transform="rotate(30 120 75)"/>
  <!-- Body -->
  <ellipse cx="100" cy="115" rx="25" ry="35" fill="#1e293b"/>
  <!-- Head -->
  <circle cx="100" cy="78" r="18" fill="#0f172a"/>
  <!-- Red Eyes -->
  <circle cx="90" cy="74" r="8" fill="#dc2626"/>
  <circle cx="110" cy="74" r="8" fill="#dc2626"/>
</svg>''',

    "30_Aankh.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#f0f9ff"/>
  <!-- Eye Shape -->
  <path d="M30 100 Q100 35 170 100 Q100 165 30 100 Z" fill="#ffffff" stroke="#0284c7" stroke-width="4"/>
  <!-- Iris -->
  <circle cx="100" cy="100" r="32" fill="#2563eb"/>
  <!-- Pupil -->
  <circle cx="100" cy="100" r="16" fill="#0f172a"/>
  <!-- Reflection -->
  <circle cx="90" cy="90" r="6" fill="#ffffff"/>
</svg>''',

    "31_Naak.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#fff7ed"/>
  <!-- Nose Profile/Icon -->
  <path d="M90 40 L90 120 Q90 145 120 140 Q135 135 125 120 Q110 125 105 110 L105 40 Z" fill="#fdba74" stroke="#ea580c" stroke-width="3"/>
  <!-- Nostril -->
  <ellipse cx="115" cy="132" rx="6" ry="4" fill="#9a3412"/>
</svg>''',

    "32_Rang.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#faf5ff"/>
  <!-- Artist Palette -->
  <path d="M50 60 C100 30 170 50 170 110 C170 160 120 170 80 150 C50 135 30 90 50 60 Z" fill="#d97706"/>
  <!-- Thumb Hole -->
  <circle cx="140" cy="130" r="12" fill="#faf5ff"/>
  <!-- Paint Blobs -->
  <circle cx="70" cy="75" r="12" fill="#ef4444"/>
  <circle cx="105" cy="65" r="12" fill="#3b82f6"/>
  <circle cx="140" cy="80" r="12" fill="#22c55e"/>
  <circle cx="75" cy="115" r="12" fill="#eab308"/>
</svg>''',

    "33_Titli.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#fdf4ff"/>
  <!-- Butterfly Wings Top -->
  <path d="M100 100 Q40 30 30 80 Q25 120 100 105 Z" fill="#c084fc"/>
  <path d="M100 100 Q160 30 170 80 Q175 120 100 105 Z" fill="#c084fc"/>
  <!-- Butterfly Wings Bottom -->
  <path d="M100 105 Q45 130 55 165 Q85 175 100 115 Z" fill="#e879f9"/>
  <path d="M100 105 Q155 130 145 165 Q115 175 100 115 Z" fill="#e879f9"/>
  <!-- Body -->
  <rect x="96" y="70" width="8" height="70" rx="4" fill="#4c1d95"/>
  <!-- Antennae -->
  <path d="M98 70 Q85 45 75 50" stroke="#4c1d95" stroke-width="2" fill="none"/>
  <path d="M102 70 Q115 45 125 50" stroke="#4c1d95" stroke-width="2" fill="none"/>
</svg>''',

    "34_Anda.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#f8fafc"/>
  <!-- Egg Shape -->
  <path d="M100 35 C135 35 155 85 155 125 C155 160 130 175 100 175 C70 175 45 160 45 125 C45 85 65 35 100 35 Z" fill="#fef3c7" stroke="#fde047" stroke-width="3"/>
  <!-- Shadow/Shading -->
  <path d="M115 50 C135 70 145 105 142 140" fill="none" stroke="#f59e0b" stroke-width="4" stroke-linecap="round" opacity="0.4"/>
</svg>''',

    "35_Oont.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#fef3c7"/>
  <!-- Camel Hump & Body -->
  <path d="M45 135 L55 105 Q75 60 95 100 Q120 55 145 105 L160 135 Z" fill="#d97706"/>
  <!-- Neck & Head -->
  <path d="M45 135 Q30 90 40 60 L60 55 L55 85 L65 110 Z" fill="#b45309"/>
  <!-- Legs -->
  <rect x="60" y="135" width="10" height="45" rx="3" fill="#92400e"/>
  <rect x="80" y="135" width="10" height="45" rx="3" fill="#92400e"/>
  <rect x="125" y="135" width="10" height="45" rx="3" fill="#92400e"/>
  <rect x="145" y="135" width="10" height="45" rx="3" fill="#92400e"/>
</svg>'''
}

for filename, content in svgs.items():
    filepath = IMAGES_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print(f"Successfully generated {len(svgs)} SVG picture files in {IMAGES_DIR}")
