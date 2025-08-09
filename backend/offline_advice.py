"""Rule-based advice used when no LLM is configured.

Each class the model can predict is matched to a crop and a condition, and the
tables below fill in the same eight sections the LLM prompt asks for.
"""

from __future__ import annotations

# crop keywords
CROPS: list[tuple[tuple[str, ...], str]] = [
    (("sugarcane",), "Sugarcane"),
    (("cotton",), "Cotton"),
    (("wheat",), "Wheat"),
    (("maize", "corn"), "Maize"),
    (("rice", "paddy", "tungro", "brownspot", "blast"), "Rice"),
]

# First match wins, so specific entries ("red cotton bug") come before
# general ones ("bug").
CONDITIONS: list[tuple[tuple[str, ...], dict[str, str]]] = [
    (
        ("healthy",),
        {
            "name": "No disease detected",
            "description": "The leaf appears healthy, with no visible lesions, discolouration or pest damage.",
            "causes": "Not applicable, no pathogen or pest was identified.",
            "symptoms": "Uniform green colour, intact leaf margins, no spots, streaks or webbing.",
            "prevention": "Keep up the current routine: balanced nutrition, even irrigation, and weekly scouting of 10 random plants per acre.",
            "treatment": "No treatment needed. Do not spray preventively, unnecessary pesticide raises cost and drives resistance.",
            "environment": "Not applicable.",
        },
    ),
    (
        ("yellow rust", "brown leaf rust", "black rust", "redrust", "rust"),
        {
            "name": "Rust (fungal)",
            "description": "A fungal disease producing powdery pustules that rupture the leaf surface and release spores. It spreads on wind over long distances and can cut yield sharply when it reaches the flag leaf.",
            "causes": "Puccinia species. Spores arrive on wind and germinate on leaves that stay wet for several hours.",
            "symptoms": "Raised yellow, orange or reddish-brown pustules in stripes or scattered patches. Rubbing a leaf leaves coloured powder on the finger. Severe infection dries the leaf from the tip.",
            "prevention": "Sow resistant varieties, avoid late sowing and excess nitrogen, destroy volunteer plants between seasons, and keep rows oriented for airflow.",
            "treatment": "Apply a triazole or strobilurin fungicide (for example propiconazole 25 EC at 0.1%) at first pustule sighting, repeating after 15 days if it spreads. Protect the flag leaf first, it contributes most to grain fill.",
            "environment": "Cool, humid weather of roughly 15-22 °C with dew, light drizzle or heavy irrigation.",
        },
    ),
    (
        ("scab", "head blight"),
        {
            "name": "Scab / Fusarium head blight (fungal)",
            "description": "A fungal infection of the ear during flowering that bleaches spikelets and shrivels the grain. Infected grain can carry deoxynivalenol (DON), a mycotoxin that makes it unsafe for food or feed.",
            "causes": "Fusarium graminearum and related species, surviving on maize and wheat residue left on the soil surface and splashed up onto the ear at flowering.",
            "symptoms": "Premature bleaching of one or more spikelets while the rest of the ear stays green; pink-orange spore masses at the glume base in humid weather; shrivelled, chalky, lightweight 'tombstone' kernels.",
            "prevention": "Avoid sowing wheat straight after maize, since both host the fungus; bury or remove residue; and stagger varieties so the whole field does not flower in a single wet week.",
            "treatment": "Timing is critical: spray tebuconazole or prothioconazole at early flowering (anthesis), when anthers first appear. Sprays applied after symptoms show give little control. Harvest promptly, set the combine fan high to blow out light infected kernels, and keep scabby grain separate.",
            "environment": "Warm, wet weather of roughly 25-30 °C with rain or heavy dew during flowering.",
        },
    ),
    (
        ("powdery mildew",),
        {
            "name": "Powdery mildew (fungal)",
            "description": "A surface fungus that coats leaves in white powder, blocking light and reducing photosynthesis.",
            "causes": "Blumeria/Erysiphe species, favoured by dense canopies and moderate temperatures.",
            "symptoms": "White to grey powdery patches on the upper leaf surface, later turning dull grey with black specks. Leaves yellow and dry.",
            "prevention": "Widen plant spacing for airflow, avoid excess nitrogen, and choose tolerant varieties.",
            "treatment": "Spray wettable sulphur at 0.2%, or a triazole fungicide if infection is advanced. Repeat after 12-15 days if needed.",
            "environment": "Dry days with cool, humid nights at roughly 16-24 °C. Unlike most fungi, it does not need standing leaf water.",
        },
    ),
    (
        ("leaf blight", "becterial blight", "bacterial_blight", "bacterial blight", "blight"),
        {
            "name": "Blight (bacterial or fungal)",
            "description": "Rapidly spreading lesions that kill leaf tissue in patches, often starting at the margins and moving inward.",
            "causes": "Xanthomonas bacteria in the bacterial form, or Alternaria/Helminthosporium fungi in the fungal form. Both enter through wounds and natural openings and travel in splashing water.",
            "symptoms": "Water-soaked streaks or grey-green patches that enlarge and turn straw-coloured, often with a yellow halo. Bacterial blight may ooze droplets in the morning.",
            "prevention": "Use certified disease-free seed, treat seed before sowing, rotate out of the host crop for a season, avoid working the field when foliage is wet, and drain standing water.",
            "treatment": "For bacterial blight, spray copper oxychloride at 0.3% with streptomycin sulphate; for the fungal form, use mancozeb at 0.25%. Remove and destroy severely affected plants rather than composting them.",
            "environment": "Warm, wet weather of roughly 25-30 °C with heavy rain, high humidity or overhead irrigation.",
        },
    ),
    (
        ("flag smut", "leaf smut", "smut"),
        {
            "name": "Smut (fungal)",
            "description": "A systemic fungus that replaces plant tissue with masses of black spores, often destroying the grain or forming streaks along the leaf.",
            "causes": "Urocystis/Ustilago species, carried on seed and surviving in soil for years.",
            "symptoms": "Grey-black streaks between leaf veins that rupture into sooty powder, stunted plants, and heads that fail to fill.",
            "prevention": "This is primarily a seed-borne disease, so seed treatment is the control: use carboxin or carbendazim before sowing. Follow a three-year rotation and never re-sow seed from an affected field.",
            "treatment": "There is no effective rescue spray once a plant is systemically infected. Pull and burn affected plants before the spore masses rupture, and treat seed next season.",
            "environment": "Cool, moist soil at sowing, especially with deep sowing that slows emergence.",
        },
    ),
    (
        ("redrot", "red rot"),
        {
            "name": "Red rot (fungal)",
            "description": "A serious fungal disease of sugarcane that rots the internal stalk tissue and collapses the cane.",
            "causes": "Colletotrichum falcatum, spread through infected setts and soil, entering via borer holes and cut ends.",
            "symptoms": "Leaves yellow and dry from the top down; split canes show reddened internal tissue crossed by white patches, with a sour alcoholic smell.",
            "prevention": "Plant resistant varieties and healthy setts from a disease-free nursery, treat setts in hot water or a carbendazim dip, and avoid ratooning an affected crop.",
            "treatment": "No cure exists for an infected stool. Uproot and burn affected clumps, drench the gap with carbendazim at 0.1%, and do not plant cane there next season.",
            "environment": "Warm, waterlogged conditions of roughly 25-30 °C, worsened by borer damage that opens entry wounds.",
        },
    ),
    (
        ("rice blast", "blast"),
        {
            "name": "Rice blast (fungal)",
            "description": "One of the most damaging rice diseases, producing spindle-shaped lesions that can kill the whole panicle neck.",
            "causes": "Magnaporthe oryzae, favoured by high nitrogen and prolonged leaf wetness.",
            "symptoms": "Diamond or spindle-shaped lesions with grey centres and brown margins; blackened, broken panicle necks that leave empty grain.",
            "prevention": "Split nitrogen into smaller doses rather than one heavy application, keep a thin film of water rather than alternating wet and dry, and sow resistant varieties.",
            "treatment": "Spray tricyclazole at 0.06% or carbendazim at 0.1% at first lesions, and again at panicle emergence if weather stays humid.",
            "environment": "Night temperatures of 20-25 °C with long dew periods, overcast days and excess nitrogen.",
        },
    ),
    (
        ("brownspot", "brown spot", "gray_leaf_spot", "gray leaf spot", "leaf spot"),
        {
            "name": "Leaf spot (fungal)",
            "description": "Discrete necrotic spots that merge as they enlarge, reducing the green area available for photosynthesis.",
            "causes": "Bipolaris, Cercospora or related fungi, often worse on nutrient-starved or drought-stressed plants.",
            "symptoms": "Round to oval brown spots, sometimes with a darker ring or yellow halo, densest on older lower leaves.",
            "prevention": "Correct the underlying stress: leaf spot is often a symptom of potassium deficiency or uneven watering. Remove crop residue after harvest and rotate crops.",
            "treatment": "Spray mancozeb at 0.25% or a propiconazole product, and apply potassium if a soil test shows a deficit.",
            "environment": "Warm, humid weather of roughly 25-30 °C with frequent light rain.",
        },
    ),
    (
        ("anthracnose",),
        {
            "name": "Anthracnose (fungal)",
            "description": "A fungus causing sunken dark lesions on leaves, stems and bolls, often with pink spore masses in wet weather.",
            "causes": "Colletotrichum species, carried on seed and crop debris and splashed by rain.",
            "symptoms": "Small reddish-brown spots that enlarge into sunken grey lesions with dark borders; seedling stems girdled at the base; bolls rotting from the tip.",
            "prevention": "Use treated, certified seed, avoid dense planting, and plough in or remove residue after harvest.",
            "treatment": "Spray carbendazim at 0.1% or mancozeb at 0.25%, repeating at 10-14 day intervals while wet weather lasts.",
            "environment": "Warm and very wet, roughly 25-30 °C with extended rainfall.",
        },
    ),
    (
        ("mosaic",),
        {
            "name": "Mosaic virus",
            "description": "A viral infection that mottles the leaf in light and dark green patches and stunts growth. It cannot be cured.",
            "causes": "Sugarcane mosaic virus and relatives, spread by aphids and by cutting tools and infected planting material.",
            "symptoms": "Irregular pale green, yellow and normal-green stripes running along the leaf; narrowed leaves and shortened internodes.",
            "prevention": "Plant virus-free certified setts or seed, control the aphid vectors that spread it, and disinfect knives between stools.",
            "treatment": "No chemical controls a virus. Remove and destroy infected plants to cut the inoculum, and manage aphids to slow spread.",
            "environment": "Any conditions that favour aphid activity, particularly warm, dry spells.",
        },
    ),
    (
        ("leaf curl",),
        {
            "name": "Leaf curl virus",
            "description": "A whitefly-transmitted virus that curls and thickens leaves and severely stunts the plant.",
            "causes": "Begomovirus group, transmitted by the whitefly Bemisia tabaci. Not seed-borne in most hosts.",
            "symptoms": "Upward or downward curling of leaf margins, thickened leathery leaves with swollen veins, enations on the underside, and stunted bushy growth.",
            "prevention": "Control whitefly early, use tolerant varieties, remove alternate weed hosts around field bunds, and install yellow sticky traps at 10-12 per acre.",
            "treatment": "The virus itself cannot be treated. Rogue out infected plants and manage whitefly with a systemic insecticide such as a neonicotinoid, rotating chemistries to avoid resistance.",
            "environment": "Hot, dry weather of 30-35 °C, which favours rapid whitefly multiplication.",
        },
    ),
    (
        ("tungro",),
        {
            "name": "Rice tungro disease (viral)",
            "description": "A viral complex spread by green leafhoppers that stunts rice and turns leaves yellow-orange.",
            "causes": "Two viruses acting together, transmitted by green leafhoppers feeding on infected plants.",
            "symptoms": "Yellow to orange discolouration starting at the leaf tip, stunted plants, reduced tillering and partly filled grain.",
            "prevention": "Synchronise planting across the area, sow resistant varieties, and avoid staggered nurseries that give leafhoppers a continuous host.",
            "treatment": "No cure for infected plants. Remove them and manage leafhopper populations; monitor with a light trap and treat only when counts exceed threshold.",
            "environment": "Warm weather with overlapping rice crops that sustain the leafhopper vector.",
        },
    ),
    (
        ("wilt",),
        {
            "name": "Wilt (soil-borne fungal or bacterial)",
            "description": "A vascular infection that blocks water movement, so the plant wilts even in moist soil.",
            "causes": "Fusarium or Verticillium fungi, or Ralstonia bacteria, persisting in soil for years and entering through roots.",
            "symptoms": "Yellowing and drooping that often affects one side of the plant first; a cut stem shows browned vascular tissue; the plant does not recover overnight.",
            "prevention": "This lives in the soil, so rotation and resistant varieties matter most. Solarise nursery beds, improve drainage, and add well-rotted organic matter plus Trichoderma to suppress the pathogen.",
            "treatment": "Soil drenching with carbendazim at 0.1% around affected stools can slow spread, but infected plants rarely recover. Remove them with the root ball intact.",
            "environment": "Warm soil of 25-30 °C that is waterlogged or poorly drained.",
        },
    ),
    (
        ("ear rot", "bollrot", "boll rot"),
        {
            "name": "Rot of the harvested organ (fungal)",
            "description": "Fungal decay of the cob or boll itself, which directly destroys the marketable part of the crop and can leave mycotoxins behind.",
            "causes": "Fusarium, Aspergillus or Diplodia species, usually entering through insect feeding holes or hail damage.",
            "symptoms": "Pink, white or blue-green mould between kernels or inside the boll; discoloured, lightweight, shrivelled produce.",
            "prevention": "Control the borers and bollworms that open entry wounds, avoid dense canopies that stay damp, and harvest promptly at maturity rather than leaving the crop standing.",
            "treatment": "Fungicides give poor control once rot has set in. Harvest and dry affected produce separately, keep moisture below 14% in storage, and do not feed badly mouldy grain to livestock.",
            "environment": "Wet, humid weather during maturity and delayed harvest.",
        },
    ),
    (
        ("aphid",),
        {
            "name": "Aphid infestation (sap-sucking pest)",
            "description": "Soft-bodied insects that colonise shoots and leaf undersides, drain sap, and spread viruses.",
            "causes": "Colonies build rapidly in warm, dry weather, especially where nitrogen has been applied heavily.",
            "symptoms": "Clusters of small green, black or brown insects under leaves and on tender shoots; curled leaves; sticky honeydew turning into black sooty mould; ants trailing up stems.",
            "prevention": "Conserve natural enemies: ladybird beetles, syrphid flies and lacewings usually control aphids unless broad-spectrum sprays have killed them. Avoid excess nitrogen and use yellow sticky traps to monitor.",
            "treatment": "Start with a 5% neem seed kernel extract or insecticidal soap spray directed at leaf undersides. Escalate to a systemic such as imidacloprid only if colonies exceed roughly 15-20 aphids per leaf.",
            "environment": "Warm, dry weather of 20-30 °C; populations crash in heavy rain.",
        },
    ),
    (
        ("whitefly",),
        {
            "name": "Whitefly infestation (sap-sucking pest)",
            "description": "Tiny white-winged insects on leaf undersides that drain sap and transmit leaf curl and other viruses.",
            "causes": "Rapid multiplication in hot dry weather, worsened by continuous cropping and insecticide resistance.",
            "symptoms": "Clouds of small white insects rising when the canopy is disturbed; yellow stippled leaves; honeydew and sooty mould; virus symptoms appearing weeks later.",
            "prevention": "Install yellow sticky traps at 10-12 per acre, remove weed hosts, avoid over-fertilising with nitrogen, and never spray the same chemistry twice in a row.",
            "treatment": "Spray neem oil at 0.5% or a detergent-based soap solution on leaf undersides, where the nymphs sit. For heavy pressure use diafenthiuron or spiromesifen, rotating modes of action.",
            "environment": "Hot, dry weather of 30-35 °C.",
        },
    ),
    (
        ("mealy bug", "mealybug"),
        {
            "name": "Mealy bug infestation (sap-sucking pest)",
            "description": "Waxy white insects that cluster at nodes and leaf axils, drain sap and secrete honeydew.",
            "causes": "Spread by ants, wind, tools and infested planting material; the wax coating protects them from contact sprays.",
            "symptoms": "Cottony white masses in leaf axils and on stems, stunted bunched growth, honeydew and sooty mould, and heavy ant traffic.",
            "prevention": "Control the ants that carry and protect them, remove and burn infested plant parts, and inspect new planting material before bringing it into the field.",
            "treatment": "Add a wetting agent or 1% fish-oil rosin soap so the spray penetrates the wax, then apply neem oil or buprofezin. Spot-treat colonies rather than blanket-spraying.",
            "environment": "Warm, dry, sheltered conditions inside a dense canopy.",
        },
    ),
    (
        ("thirps", "thrips"),
        {
            "name": "Thrips infestation (rasping pest)",
            "description": "Slender insects that rasp the leaf surface and feed on the escaping sap, leaving silvered tissue.",
            "causes": "Build-up in hot dry spells; they shelter deep in buds and flowers where sprays rarely reach.",
            "symptoms": "Silvery or bronzed streaks on leaves with tiny black faecal specks, upward-curled leaf margins, and distorted buds that may drop.",
            "prevention": "Use blue sticky traps to monitor, irrigate adequately since drought-stressed plants suffer most, and avoid nitrogen excess.",
            "treatment": "Spray neem seed kernel extract at 5%, or fipronil or spinosad for severe infestations. Target early morning when thrips are active on the surface.",
            "environment": "Hot, dry weather above 30 °C with little rain.",
        },
    ),
    (
        ("mite",),
        {
            "name": "Mite infestation (arachnid pest)",
            "description": "Microscopic spider relatives that feed on leaf undersides, causing stippling and fine webbing.",
            "causes": "Explosive build-up in hot dry weather, very often triggered by a pyrethroid spray that killed the predatory mites keeping them in check.",
            "symptoms": "Fine yellow-white speckling that merges into bronzed patches; delicate webbing under leaves; tiny moving dots visible with a hand lens.",
            "prevention": "Avoid pyrethroids where mites are a known problem, maintain adequate irrigation, and keep field borders free of dusty weed hosts.",
            "treatment": "Use a true acaricide (dicofol, propargite or spiromesifen), not a general insecticide, which will make the problem worse. A forceful water spray on leaf undersides helps in light cases.",
            "environment": "Hot, dry, dusty weather above 30 °C with low humidity.",
        },
    ),
    (
        ("bollworm", "army worm", "armyworm", "stem borer", "stem fly", "borer"),
        {
            "name": "Caterpillar or borer infestation (chewing pest)",
            "description": "Larvae that chew foliage or tunnel into stems, bolls and cobs, feeding inside where sprays cannot reach them.",
            "causes": "Moths lay eggs on the crop; the damaging stage is the larva, which bores in within a few days of hatching.",
            "symptoms": "Ragged chewed leaves, entry holes ringed with sawdust-like frass, 'dead heart' in young shoots, and hollowed bolls or cobs that drop early.",
            "prevention": "Timing is everything: install pheromone traps at 5 per acre and scout weekly, because control only works before the larva enters the plant. Destroy stubble after harvest, and plant trap or border crops.",
            "treatment": "At egg-laying or early larval stage, apply Bacillus thuringiensis or a neem formulation; for established larvae use chlorantraniliprole or emamectin benzoate. Hand-pick and crush large larvae in small plots. Once larvae are inside the stem or boll, no spray will reach them.",
            "environment": "Warm weather of 25-35 °C; some species migrate in large numbers after the first rains.",
        },
    ),
    (
        ("red cotton bug", "bug"),
        {
            "name": "Red cotton bug (sap-sucking pest)",
            "description": "A conspicuous red bug that feeds on developing seed, staining the lint and reducing seed viability.",
            "causes": "Migrates into the crop at boll formation and aggregates on open bolls and fallen seed.",
            "symptoms": "Clusters of bright red bugs on bolls, yellow-stained lint, shrivelled seed, and poor germination from saved seed.",
            "prevention": "Clear fallen bolls and seed from the field, which is where they aggregate, and keep bunds free of alternate hosts.",
            "treatment": "Hand-collect and destroy the aggregations, which is often enough. If numbers are high, spray a malathion or quinalphos product at boll formation.",
            "environment": "Warm, dry weather during boll maturity.",
        },
    ),
]

GENERIC_CONDITION: dict[str, str] = {
    "name": "Unrecognised condition",
    "description": "The classifier returned a label this offline knowledge base does not have a specific entry for.",
    "causes": "Undetermined without further inspection.",
    "symptoms": "Compare the affected leaf against a healthy one from the same field, noting lesion shape, colour and whether damage starts at the margin, tip or vein.",
    "prevention": "Follow general crop hygiene: certified seed, crop rotation, balanced nutrition, good drainage, and weekly scouting.",
    "treatment": "Take a fresh sample to the nearest Krishi Vigyan Kendra or state agriculture extension officer before spraying anything. Treating the wrong cause wastes money and can worsen the problem.",
    "environment": "Undetermined.",
}


# Labels that don't name the crop
LABEL_CROPS: dict[str, str] = {
    "common_rust": "Maize (common rust is the maize-specific rust, Puccinia sorghi)",
    "gray_leaf_spot": "Maize (Cercospora zeae-maydis)",
    "flag smut": "Wheat (Urocystis agropyri)",
    "leaf smut": "Rice (Entyloma oryzae)",
    "leaf curl": "Cotton (cotton leaf curl virus, spread by whitefly)",
    "wilt": "Cotton and sugarcane among the crops this model covers; wilt pathogens also attack many others",
    "army worm": "Rice, maize, wheat and sugarcane (armyworms feed on most cereal crops)",
}


def identify_crop(disease_name: str) -> str | None:
    """Return the crop a class label refers to, if it can be determined."""
    lowered = disease_name.lower()
    for keywords, crop in CROPS:
        if any(keyword in lowered for keyword in keywords):
            return crop
    return LABEL_CROPS.get(lowered.strip())


def identify_condition(disease_name: str) -> dict[str, str]:
    """Guidance entry for a class label (generic advice if nothing matches)."""
    lowered = disease_name.lower()
    for keywords, condition in CONDITIONS:
        if any(keyword in lowered for keyword in keywords):
            return condition
    return GENERIC_CONDITION


def build_disease_report(disease_name: str, confidence: float | None = None) -> str:
    """Build the eight-section markdown report for a classified disease."""
    condition = identify_condition(disease_name)
    crop = identify_crop(disease_name)

    header = f"## {disease_name}"
    if confidence is not None:
        header += f"\n\n**Model confidence:** {confidence:.0%}"
        if confidence < 0.6:
            header += (
                "  \n> ⚠️ This is a low-confidence prediction. Confirm against the "
                "symptoms below before acting on it."
            )

    affected = crop or "Identify the affected crop from the field before treating."

    return f"""{header}

### 1. Disease name
{condition["name"]}

### 2. Description
{condition["description"]}

### 3. Common causes
{condition["causes"]}

### 4. Affected crops
{affected}

### 5. Symptoms to confirm
{condition["symptoms"]}

### 6. Prevention
{condition["prevention"]}

### 7. Recommended treatment
{condition["treatment"]}

### 8. Conditions that promote it
{condition["environment"]}

---
_Offline advice from the built-in knowledge base (no language model is
configured). Dosages are indicative, follow the product label and check with
your local extension officer before spraying._
"""


# Simple keyword replies for chat when there's no LLM
_CHAT_TOPICS: list[tuple[tuple[str, ...], str]] = [
    (
        ("water", "irrigat", "moisture", "drought", "dry"),
        "Check soil moisture by hand before irrigating: squeeze soil from 15cm "
        "down, if it holds together it still has water. Irrigate early morning "
        "or evening to cut evaporation, and make sure water drains away rather "
        "than standing, since waterlogged roots invite rot and wilt.",
    ),
    (
        ("fertil", "nitrogen", "urea", "nutrient", "npk", "yellow leaves"),
        "Split nitrogen into two or three smaller doses instead of one heavy "
        "application. A single large dose pushes soft growth that aphids, "
        "whitefly and rust all prefer. Uniform yellowing of older leaves usually "
        "means nitrogen is short; yellowing between the veins of younger leaves "
        "points to iron or zinc. A soil test is cheaper than a wrong guess.",
    ),
    (
        ("spray", "pesticid", "insecticid", "fungicid", "dose", "chemical"),
        "Spray only after scouting confirms the pest is above threshold, and "
        "rotate chemistries between sprays so resistance does not build. Direct "
        "the nozzle at leaf undersides, where most sap-sucking pests actually "
        "sit. Never mix products without checking compatibility, and always wear "
        "a mask and full sleeves.",
    ),
    (
        ("pest", "insect", "worm", "caterpillar", "bug"),
        "Identify the pest before treating: chewing damage (ragged leaves, entry "
        "holes with frass) needs a different product from sucking damage "
        "(stippling, curling, sticky honeydew). Pheromone traps tell you when "
        "moths are laying, which is the only window where spraying for borers "
        "actually works. Once the larva is inside the stem, no spray reaches it.",
    ),
    (
        ("soil", "ph", "organic", "compost"),
        "Add well-rotted farmyard manure or compost each season to improve "
        "structure and water holding, it matters more than any single "
        "fertiliser dose. Most field crops want a pH between 6.0 and 7.5; get "
        "the soil tested every two or three years rather than guessing.",
    ),
    (
        ("weather", "rain", "temperature", "forecast", "humid"),
        "Humid weather with long dew periods favours fungal disease, so scout "
        "more often after rain and avoid working the field while foliage is wet, "
        "which spreads bacteria plant to plant. Hot, dry spells instead favour "
        "mites, thrips and whitefly. Open the Reports page for the current "
        "readings at your field.",
    ),
    (
        ("disease", "spot", "rust", "blight", "fungus", "leaf"),
        "Upload a clear photo of an affected leaf using the image button and the "
        "classifier will identify the most likely disease and the treatment for "
        "it. Photograph a single leaf in daylight against a plain background, "
        "with the damage filling most of the frame.",
    ),
]


def answer_question(question: str, has_context: bool = False) -> str:
    """Best-effort rule-based reply for a free-text question."""
    lowered = question.lower()

    for keywords, reply in _CHAT_TOPICS:
        if any(keyword in lowered for keyword in keywords):
            body = reply
            break
    else:
        body = (
            "I can help with crop disease, irrigation, fertiliser, pests, soil and "
            "weather. Two things work without any setup: upload a leaf photo with "
            "the image button to get a diagnosis, and open the Reports page for "
            "your field's latest conditions."
        )

    if has_context:
        body += (
            "\n\nYour latest field report is loaded, so also check the Reports "
            "page for the specific readings from your plot."
        )

    return (
        f"{body}\n\n---\n_Offline reply from the built-in knowledge base. Set "
        "`GEMINI_API_KEY` and `GEMINI_MODEL` (or `OLLAMA_MODEL`) in `backend/.env` "
        "to enable full conversational answers._"
    )
