<div align="center">

# 🩺 EnterMedSchool Glossary — Enhanced Edition ⚡

<p align="center">
  <b>The Complete High-Yield Medical Dictionary Engine for Anki Desktop</b><br>
  <i>Designed for Medical Students & Doctors Preparing for USMLE, PLAB, UPSC CMS, & Board Exams</i>
</p>

<!-- EnterMedSchool Styled Badges -->
<p align="center">
  <a href="https://apps.ankiweb.net"><img src="https://img.shields.io/badge/Anki-2.1%2B%20%7C%2023%2B%20%7C%2024%2B-6C5CE7?style=for-the-badge&logo=anki&logoColor=white" alt="Anki Compatibility"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-GPL--3.0-a29bfe?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/safevoice009/anki-glossary-enhanced/releases"><img src="https://img.shields.io/badge/Version-v2.0.0--Enhanced-00b894?style=for-the-badge" alt="Release"></a>
  <a href="https://entermedschool.com"><img src="https://img.shields.io/badge/EnterMedSchool-Chunky%20Theme-fd79a8?style=for-the-badge" alt="Theme"></a>
</p>

</div>

---

> [!IMPORTANT]
> ### 🙏 Credits, APIs & Open-Source Acknowledgments
> 
> * **Original Concept & Base Code:** Created by **Ari Horesh** and the team at **[EnterMedSchool](https://entermedschool.com)** ([Original Repository](https://github.com/entermedschool/anki-glossary)).
> * **Live Online Dictionary Data & API:** Powered by the open-access **[Wikimedia REST API](https://en.wikipedia.org/api/rest_v1/)** provided by the **Wikimedia Foundation** and Wikipedia contributors worldwide.
> * **Integration & Enhanced Configuration:** Configured and maintained by **[safevoice009](https://github.com/safevoice009)** on GitHub to integrate live Wikipedia API queries, universal double-click lookup, high-yield exam trap extraction, and movable window capabilities.
> * **License:** Open Source (GPL-3.0). All base code credits belong to EnterMedSchool, and data credits to Wikimedia Foundation.

---

## 🧠 System Architecture & Workflow Mindmap

```mermaid
flowchart TD
    classDef cardStyle fill:#6C5CE7,color:#ffffff,stroke:#1a1a2e,stroke-width:3px;
    classDef engineStyle fill:#7E22CE,color:#ffffff,stroke:#1a1a2e,stroke-width:3px;
    classDef apiStyle fill:#00b894,color:#ffffff,stroke:#1a1a2e,stroke-width:3px;
    classDef trapStyle fill:#fd79a8,color:#ffffff,stroke:#1a1a2e,stroke-width:3px;
    classDef windowStyle fill:#FFD93D,color:#1a1a2e,stroke:#1a1a2e,stroke-width:3px;

    A["🃏 Anki Flashcard Review\n(USMLE / PLAB / UPSC / Deck)"] ::: cardStyle -->|👆 Double-Click ANY Word| B["⚡ EnterMedSchool Event Listener"] ::: engineStyle
    
    B --> C{"🔍 Search Local Glossary DB?\n(564+ Terms & 2695 Patterns)"}
    
    C -->|✅ Term Found| D["📦 Load Local Offline Definition"] ::: engineStyle
    C -->|🌐 Term Missing| E["🌐 Query Wikipedia Medical REST API\n(Real-Time Live Search)"] ::: apiStyle
    
    D --> F["💡 High-Yield Exam Traps & Mnemonics Engine"] ::: trapStyle
    E --> F
    
    F --> G["🪟 Render Movable Desktop Window\n(Pinned WindowStaysOnTopHint)"] ::: windowStyle
```

---

## 🎨 Chunky EnterMedSchool Aesthetic Features

* **🌈 Official EnterMedSchool Chunky Theme**: Chunky black borders (`3px solid #1a1a2e`), drop shadows (`4px 4px 0 #1a1a2e`), and vibrant gradients matching `https://www.entermedschool.com/`.
* **🌐 Universal Double-Click Lookup**: Double-click ANY word or phrase on ANY card to fetch live medical summaries over the internet via the **Wikipedia Medical REST API**.
* **💡 High-Yield Exam Traps Engine**: Automatically synthesizes medical board exam traps, precautions, and mnemonics (e.g. *Folate masking B12*, *Milk-Alkali Syndrome*, *Iron toxicity*, *CAPTOPRIL*).
* **🔤 Smart Suffix Auto-Matcher**: Matches singular terms to plural forms (`-s`, `-es`) and tenses (`-ed`, `-ing`) automatically.
* **🪟 Movable Desktop Window**: Standalone top-level window (`WindowStaysOnTopHint`) that stays pinned on top of Anki while reviewing.

---

## 📊 Feature Comparison Table

| Component | Original EnterMedSchool Add-on | Enhanced Community Edition |
| :--- | :--- | :--- |
| **🌐 Medical Dictionary** | ~450 fixed local terms | **100% Unlimited** (Live Wikipedia Medical REST API Fallback) |
| **💡 Exam Traps & Mnemonics** | Template placeholders | **Dynamic Exam Trap & Pearl Synthesizer** |
| **🔤 Suffix Engine** | Strict exact match | **Smart Suffix Engine** (`-s`, `-es`, `-ed`, `-ing`) |
| **🪟 Desktop Window** | Fixed frameless popup | **Movable Window** (`WindowStaysOnTopHint`) |
| **👆 Trigger** | Pre-highlighted terms only | **Universal Double-Click** on any word on any card |
| **🎨 Theme & Design** | Standard EnterMedSchool theme | **Chunky EnterMedSchool Website Theme** |

---

## 📥 Installation

1. Download **`Medical_Terms_Glossary_Instant_Dictionary_Enhanced.zip`**.
2. Open Anki → **Tools > Add-ons > View Files**.
3. Unzip the downloaded folder into your Anki add-ons directory.
4. Restart Anki!

---

## 👨‍⚕️ Credits & License

* **Original Creator:** Ari Horesh ([EnterMedSchool](https://entermedschool.com))
* **Enhanced Edition Developer:** [safevoice009](https://github.com/safevoice009)
* **License:** [GPL-3.0 License](LICENSE)
