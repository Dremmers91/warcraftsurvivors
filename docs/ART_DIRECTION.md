# Art direction — Elwynn Chronicle

Use original detailed pixel art at a slightly elevated 3/4 angle. Fantasy silhouettes should read immediately at the actual game zoom: broad plate shoulders and a two-handed holy hammer for Paladin; asymmetric aggressive plate and a large axe for Warrior; tall blue robes/staff for Mage; a hood, leather cape and bow for Hunter; angular black-violet robes and a fel implement for Warlock; ivory ceremonial robes and a sun-shaped staff for Priest. Character shape changes must go beyond a shared silhouette with another color.

Principal humanoid source height is 56–64 pixels, with feet anchored near the bottom of an 80 × 80 transparent frame. Paladin and Warrior are broader than casters. Kobolds are shorter, hunched miners; wolves are low, long quadrupeds; bandits have red scarves and leather weapons. Keep source pixels crisp at integer scales, using a 1280 × 720 logical game surface. Preserve consistent feet anchors across animation frames and separate art bounds from collision radii.

Use a deep ink outline, selective warm edge light from upper left, cool metal shadows, clustered pixels and readable midtones. Holy assets use ivory/silver/gold; forest materials use moss, olive, bark and warm road earth. Red scarves distinguish Defias enemies. Avoid excessive noise, full-white bodies, identical recolored costumes, blurry interpolation and generic dots standing in for physical weapons.

Walking should display directional views and alternating foot/limb poses, while idle shows a gentle breathing/cloth/candle cycle. Hits use short precomputed bright frames; death uses a short fall/fade sequence that cannot obscure living actors. Impact flashes and gold streaks may be bright, but must leave the hammer head, handle and enemy silhouette readable. Low effects retains every actor, projectile, impact and useful indicator.

Terrain should be less saturated/contrasty than combat: grass blades in varied clusters, irregular dirt tracks, textured oak foliage, visible trunk/bark roots and restrained stones/flowers. Tree art retains the same existing trunk collision location. Reuse soft shadows below objects; Y-sort trunks/actors, then keep the player above crowded enemies.

Review generated art at native frame size and at real gameplay zoom. AI-generated sheets require slicing, alpha, alignment and pose checks; record synthesized animation limitations rather than equating a concept sheet with fully hand-authored production animation.
