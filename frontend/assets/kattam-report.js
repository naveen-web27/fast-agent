// Renders JathagamEngine results as the Kattam porutham report (DOM and downloadable text).
(function (root) {
  'use strict';

  const SOUTH_INDIAN_CELLS = { 11: [1, 1], 0: [1, 2], 1: [1, 3], 2: [1, 4], 3: [2, 4], 4: [3, 4], 5: [4, 4], 6: [4, 3], 7: [4, 2], 8: [4, 1], 9: [3, 1], 10: [2, 1] };
  const WORDS = {
    ta: {
      planets: { Sun: 'சூரியன்', Moon: 'சந்திரன்', Mars: 'செவ்வாய்', Mercury: 'புதன்', Jupiter: 'குரு', Venus: 'சுக்கிரன்', Saturn: 'சனி', Rahu: 'ராகு', Ketu: 'கேது' },
      short: { Sun: 'சூ', Moon: 'சந்', Mars: 'செ', Mercury: 'பு', Jupiter: 'கு', Venus: 'சு', Saturn: 'ச', Rahu: 'ரா', Ketu: 'கே', Lagna: 'ல' },
      dignity: { exalted: 'உச்சம்', debilitated: 'நீசம்', own: 'ஆட்சி' },
      retro: 'வ', lagna: 'லக்னம்', rasiChart: 'ராசி', navamsaChart: 'நவாம்சம்',
      title: 'திருமணக் கட்டப் பொருத்த அறிக்கை',
      level: { high: 'உத்தமம் — கட்டப் பொருத்தம் சிறப்பாக உள்ளது', medium: 'மத்திமம் — கவனிக்க வேண்டிய அம்சம் உள்ளது', low: 'அதமம் — முக்கியக் குறைகள் உள்ளன' },
      sections: { birth: 'பிறப்பு விவரங்கள்', charts: 'ராசி, நவாம்சக் கட்டங்கள்', planets: 'கிரக நிலைகள்', checks: 'கட்டப் பொருத்த ஆய்வு', seventh: 'களத்திர ஸ்தானம் (7-ஆம் பாவம்)', dasa: 'தசா புத்தி', star: 'நட்சத்திரச் சரிபார்ப்பு', summary: 'ஜோதிடச் சுருக்கம்', method: 'கணக்கீட்டு முறை' },
      rows: { date: 'பிறந்த தேதி', time: 'பிறந்த நேரம்', place: 'பிறந்த இடம்', coordinates: 'அட்சரேகை / தீர்க்கரேகை', timezone: 'நேர மண்டலம்', lagna: 'லக்னம்', rasi: 'ராசி', star: 'நட்சத்திரம்', ayanamsa: 'அயனாம்சம் (லஹிரி)' },
      planetHead: ['கிரகம்', 'ராசி', 'பாகை', 'நட்சத்திரம் (பாதம்)', 'நவாம்சம்', 'நிலை'],
      checks: { chevvai: 'செவ்வாய் தோஷப் பொருத்தம்', rahuKetu: 'ராகு–கேது தோஷப் பொருத்தம்', papa: 'பாப சாம்யம்', dasaSandhi: 'தசா சந்தி' },
      ok: 'பொருந்துகிறது', notOk: 'பொருந்தவில்லை', bride: 'பெண்', groom: 'பையன்', none: 'இல்லை', yes: 'உண்டு',
      house: house => `${house}-ஆம் இடம்`,
      cancel: { ownSign: 'செவ்வாய் சொந்த வீட்டில் (மேஷம் / விருச்சிகம்)', exalted: 'செவ்வாய் உச்சம் (மகரம்)', withJupiter: 'குருவுடன் சேர்க்கை' },
      chevvaiPerson: (c, w) => `செவ்வாய் லக்னத்திலிருந்து ${w.house(c.fromLagna)}, சந்திரனிலிருந்து ${w.house(c.fromMoon)}. ` + (c.raw ? (c.cancellations.length ? `தோஷ இடம்; ஆனால் ${c.cancellations.map(r => w.cancel[r]).join(', ')} என்பதால் நிவர்த்தி.` : 'செவ்வாய் தோஷம் உண்டு.') : 'செவ்வாய் தோஷம் இல்லை.'),
      chevvaiRule: 'லக்னம் அல்லது சந்திரனிலிருந்து 2, 4, 7, 8, 12-ஆம் இடங்களில் செவ்வாய் இருந்தால் தோஷம். இருவருக்கும் தோஷம் இருப்பது அல்லது இருவருக்கும் இல்லாதது பொருத்தம் (தோஷ சாம்யம்).',
      rahuPerson: (r, w) => `ராகு ${w.house(r.rahuHouse)}, கேது ${w.house(r.ketuHouse)} (லக்னத்திலிருந்து) — தோஷம் ${r.dosha ? w.yes : w.none}.`,
      rahuRule: 'லக்னத்திலிருந்து 1, 2, 7, 8-ஆம் இடங்களில் ராகு அல்லது கேது இருந்தால் தோஷம்; இருவருக்கும் சமமாக இருந்தால் பொருத்தம்.',
      papaRule: (b, g) => `பாப புள்ளிகள் — பெண்: ${b}, பையன்: ${g}. லக்னம், சந்திரன், சுக்கிரனிலிருந்து 1, 2, 4, 7, 8, 12-ஆம் இடங்களில் உள்ள சூரியன், செவ்வாய், சனி, ராகு, கேது எண்ணப்பட்டன. பையனின் பாப பலம் பெண்ணுக்குச் சமமாகவோ அதிகமாகவோ இருந்தால் பொருத்தம்.`,
      papaRefs: { lagna: 'லக்னம்', moon: 'சந்திரன்', venus: 'சுக்கிரன்' },
      dasaRule: (b, g, months) => `அடுத்த மகா தசை மாற்றம் — பெண்: ${b}, பையன்: ${g}. இடைவெளி சுமார் ${months} மாதங்கள். 12 மாதங்களுக்குள் இருவருக்கும் தசை மாறினால் தசா சந்தி எனக் கருதப்படும்.`,
      dasaName: lord => `${lord} தசை`,
      seventh: (s, w, names) => `7-ஆம் வீடு ${names.rasi[s.sign]}; அதிபதி ${w.planets[s.lord]} ${w.house(s.lordHouse)} (${names.rasi[s.lordSign]}${s.lordDignity ? ', ' + w.dignity[s.lordDignity] : ''}). 7-ல் உள்ள கிரகங்கள்: ${s.occupants.length ? s.occupants.map(p => w.planets[p]).join(', ') : w.none}.`,
      dasaRows: { birth: 'பிறப்பில் தசை', current: 'நடப்பு தசை / புத்தி', next: 'அடுத்த தசை' },
      balance: (y, m) => `இருப்பு ${y} ஆண்டு ${m} மாதம்`,
      bhukti: lord => `${lord} புத்தி`,
      starSame: (who, star) => `${who}: தேர்ந்தெடுத்த நட்சத்திரமும் பிறந்த நேரக் கணக்கும் ஒன்றே (${star}).`,
      starDiff: (who, chosen, computed) => `${who}: நீங்கள் தேர்ந்தெடுத்தது ${chosen}; பிறந்த நேரப்படி கணக்கிட்டது ${computed}. இந்த அறிக்கை கணக்கிட்ட நட்சத்திரத்தைப் பயன்படுத்துகிறது.`,
      starComputed: (who, star) => `${who}: பிறந்த நேரப்படி நட்சத்திரம் ${star}.`,
      poruthamScore: (n, level) => `பிறந்த நேரப்படி கணக்கிட்ட நட்சத்திரங்களுக்கு 12 பொருத்தம்: ${n}/12 (${level}).`,
      poruthamLevels: { high: 'உத்தமம்', medium: 'மத்திமம்', low: 'அதமம்' },
      edgeMoon: who => `${who}: சந்திரன் நட்சத்திர எல்லைக்கு மிக அருகில் உள்ளது; பிறந்த நேரத்தில் சில நிமிட மாற்றம் நட்சத்திரத்தை மாற்றக்கூடும்.`,
      edgeLagna: who => `${who}: லக்னம் ராசி எல்லைக்கு அருகில் உள்ளது; பிறந்த நேரம் துல்லியமாக இருக்க வேண்டும்.`,
      summaryOk: { chevvai: 'செவ்வாய் தோஷம் இருவருக்கும் சமநிலையில் உள்ளது.', rahuKetu: 'ராகு–கேது நிலை இருவருக்கும் சமமாக உள்ளது.', papa: 'பாப சாம்யம் சரியாக உள்ளது.', dasaSandhi: 'இருவருக்கும் ஒரே காலத்தில் தசை மாற்றம் இல்லை.' },
      summaryBad: { chevvai: 'செவ்வாய் தோஷம் ஒருவருக்கு மட்டும் உள்ளது — பாரம்பரியத்தில் இது முக்கியமாகக் கவனிக்கப்படும்.', rahuKetu: 'ராகு–கேது தோஷம் ஒருவருக்கு மட்டும் உள்ளது.', papa: 'பையனின் பாப பலம் பெண்ணைவிடக் குறைவு.', dasaSandhi: 'இருவருக்கும் 12 மாதங்களுக்குள் தசை மாறுகிறது (தசா சந்தி).' },
      finalHigh: 'நட்சத்திரப் பொருத்தமும் கட்டப் பொருத்தமும் பாரம்பரிய முறைப்படி நன்றாக அமைந்துள்ளன.',
      finalMedium: 'பொதுவாகப் பொருந்துகிறது; மேலே குறிப்பிட்ட அம்சங்களைக் கவனத்தில் கொள்ளவும்.',
      finalLow: 'முக்கியக் குறைகள் உள்ளன; முடிவெடுக்கும் முன் அனுபவமிக்க ஜோதிடரிடம் முழு ஜாதக ஆய்வு செய்வது நல்லது.',
      method: 'சாயன கிரக நிலைகள் Astronomy Engine 2.1.19 மூலம் கணக்கிடப்பட்டு, லஹிரி அயனாம்சம் கழிக்கப்பட்டது. ராகு சராசரி கணு; பாவங்கள் முழு ராசி முறை; விம்சோத்தரி தசை (365.2425 நாள் ஆண்டு). கணக்கீடு முழுவதும் உங்கள் உலாவியிலேயே நடைபெறுகிறது.',
      disclaimer: 'இது பாரம்பரிய ஜோதிட விதிகளின் அடிப்படையிலான கணக்கீடு; அறிவியல் கணிப்போ திருமண வெற்றியின் உறுதிமொழியோ அல்ல. வட்டார மரபுகளுக்கு ஏற்ப விதிகள் மாறலாம்.'
    },
    en: {
      planets: { Sun: 'Sun', Moon: 'Moon', Mars: 'Mars', Mercury: 'Mercury', Jupiter: 'Jupiter', Venus: 'Venus', Saturn: 'Saturn', Rahu: 'Rahu', Ketu: 'Ketu' },
      short: { Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me', Jupiter: 'Ju', Venus: 'Ve', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke', Lagna: 'Asc' },
      dignity: { exalted: 'exalted', debilitated: 'debilitated', own: 'own sign' },
      retro: 'R', lagna: 'Lagna', rasiChart: 'Rasi', navamsaChart: 'Navamsa',
      title: 'Jathaka Kattam compatibility report',
      level: { high: 'Uthamam — the charts are well matched', medium: 'Mathimam — one point needs attention', low: 'Athamam — significant concerns' },
      sections: { birth: 'Birth details', charts: 'Rasi and Navamsa charts', planets: 'Planetary positions', checks: 'Kattam compatibility checks', seventh: 'Kalathra sthanam (7th house)', dasa: 'Dasa and Bhukti', star: 'Nakshatra cross-check', summary: 'Astrological summary', method: 'Method' },
      rows: { date: 'Birth date', time: 'Birth time', place: 'Birthplace', coordinates: 'Latitude / longitude', timezone: 'Timezone', lagna: 'Lagna', rasi: 'Rasi', star: 'Nakshatra', ayanamsa: 'Ayanamsa (Lahiri)' },
      planetHead: ['Planet', 'Rasi', 'Degree', 'Nakshatra (pada)', 'Navamsa', 'Dignity'],
      checks: { chevvai: 'Chevvai (Mars) dosha balance', rahuKetu: 'Rahu–Ketu dosha balance', papa: 'Papa samyam', dasaSandhi: 'Dasa sandhi' },
      ok: 'Matches', notOk: 'Does not match', bride: 'Bride', groom: 'Groom', none: 'none', yes: 'present',
      house: house => `house ${house}`,
      cancel: { ownSign: 'Mars in its own sign (Mesham / Vrischikam)', exalted: 'Mars exalted (Makaram)', withJupiter: 'Mars conjunct Jupiter' },
      chevvaiPerson: (c, w) => `Mars is in ${w.house(c.fromLagna)} from Lagna and ${w.house(c.fromMoon)} from the Moon. ` + (c.raw ? (c.cancellations.length ? `A dosha position, cancelled because: ${c.cancellations.map(r => w.cancel[r]).join(', ')}.` : 'Chevvai dosha is present.') : 'No Chevvai dosha.'),
      chevvaiRule: 'Mars in houses 2, 4, 7, 8 or 12 from Lagna or Moon gives dosha. Both having it, or neither having it, is a match (dosha samyam).',
      rahuPerson: (r, w) => `Rahu in ${w.house(r.rahuHouse)}, Ketu in ${w.house(r.ketuHouse)} from Lagna — dosha ${r.dosha ? w.yes : w.none}.`,
      rahuRule: 'Rahu or Ketu in houses 1, 2, 7 or 8 from Lagna gives dosha; both being equal is a match.',
      papaRule: (b, g) => `Malefic points — bride: ${b}, groom: ${g}. Counts Sun, Mars, Saturn, Rahu and Ketu in houses 1, 2, 4, 7, 8 and 12 from Lagna, Moon and Venus. A match when the groom’s points are equal to or more than the bride’s.`,
      papaRefs: { lagna: 'Lagna', moon: 'Moon', venus: 'Venus' },
      dasaRule: (b, g, months) => `Next mahadasa change — bride: ${b}, groom: ${g}. About ${months} months apart. Both changing within 12 months is considered dasa sandhi.`,
      dasaName: lord => `${lord} dasa`,
      seventh: (s, w, names) => `7th house is ${names.rasi[s.sign]}; its lord ${w.planets[s.lord]} is in ${w.house(s.lordHouse)} (${names.rasi[s.lordSign]}${s.lordDignity ? ', ' + w.dignity[s.lordDignity] : ''}). Planets in the 7th: ${s.occupants.length ? s.occupants.map(p => w.planets[p]).join(', ') : w.none}.`,
      dasaRows: { birth: 'Dasa at birth', current: 'Current dasa / bhukti', next: 'Next dasa' },
      balance: (y, m) => `balance ${y} years ${m} months`,
      bhukti: lord => `${lord} bhukti`,
      starSame: (who, star) => `${who}: the selected Nakshatra matches the birth-time calculation (${star}).`,
      starDiff: (who, chosen, computed) => `${who}: you selected ${chosen}, but the birth time gives ${computed}. This report uses the calculated Nakshatra.`,
      starComputed: (who, star) => `${who}: Nakshatra from birth time is ${star}.`,
      poruthamScore: (n, level) => `12-porutham score for the calculated Nakshatras: ${n}/12 (${level}).`,
      poruthamLevels: { high: 'Uthamam', medium: 'Mathimam', low: 'Athamam' },
      edgeMoon: who => `${who}: the Moon is very close to a Nakshatra boundary; a few minutes’ change in birth time could change the Nakshatra.`,
      edgeLagna: who => `${who}: the Lagna is near a sign boundary; the birth time must be accurate.`,
      summaryOk: { chevvai: 'Chevvai dosha is balanced between the two.', rahuKetu: 'Rahu–Ketu placement is balanced.', papa: 'Papa samyam is satisfied.', dasaSandhi: 'No simultaneous dasa change.' },
      summaryBad: { chevvai: 'Chevvai dosha is present in only one chart — traditionally given serious weight.', rahuKetu: 'Rahu–Ketu dosha is present in only one chart.', papa: 'The groom’s malefic strength is lower than the bride’s.', dasaSandhi: 'Both change mahadasa within 12 months (dasa sandhi).' },
      finalHigh: 'Both the Nakshatra porutham and the Kattam porutham are traditionally well matched.',
      finalMedium: 'Broadly compatible; note the points mentioned above.',
      finalLow: 'Significant concerns exist; consult an experienced astrologer for a full chart review before deciding.',
      method: 'Tropical positions from Astronomy Engine 2.1.19 with Lahiri ayanamsa applied. Mean lunar node; whole-sign houses; Vimshottari dasa with a 365.2425-day year. All calculation runs in your browser.',
      disclaimer: 'This is a calculation based on traditional astrological rules, not a scientific prediction or a guarantee about a marriage. Rules vary between regional traditions.'
    }
  };

  const CHEVVAI_HOUSES = [2, 4, 7, 8, 12];
  const HIDDEN_HOUSES = [6, 8, 12];
  const WELL_PLACED_HOUSES = [1, 4, 5, 7, 9, 10];
  const TONES = { good: 'good', strong: 'good', no: 'good', mixed: 'mixed', moderate: 'mixed', cancelled: 'mixed', challenging: 'care', care: 'care', yes: 'care' };
  const ordinal = n => `${n}${n === 1 ? 'st' : n === 2 ? 'nd' : n === 3 ? 'rd' : 'th'}`;
  const PLAIN = {
    ta: {
      verdict: { high: 'நல்ல பொருத்தம்', medium: 'பொருந்தும் — சில விஷயங்களில் கவனம் தேவை', low: 'கவனமாக முடிவெடுக்கவும் — முக்கியக் குறைகள் உள்ளன' },
      verdictDetail: (stars, kattam) => `நட்சத்திரப் பொருத்தம் ${stars}/12 · கட்டப் பொருத்தம் ${kattam}/4`,
      sections: { dosha: '1. தோஷம் இருக்கிறதா?', together: '2. இருவருக்கும் பொருந்துமா?', dasa: '3. இப்போது நடக்கும் தசை, அடுத்து வரும் தசை', timeline: '4. இருவரின் தசையும் சேர்த்துப் பார்த்தால்', life: '5. எதிர்கால வாழ்க்கை', summary: '6. சுருக்கமாக', expert: 'ஜோதிடர்களுக்கான முழு விவரம் — கட்டங்கள், கிரக நிலை, கணக்கு' },
      chevvaiWhat: 'செவ்வாய் தோஷம் என்றால்: ஜாதகத்தில் செவ்வாய் கிரகம் லக்னம் அல்லது சந்திரனிலிருந்து 2, 4, 7, 8, 12-ஆம் வீடுகளில் இருப்பது. 7-ஆம் வீடு கணவன் / மனைவியைக் குறிக்கும் இடம்; அதனால் திருமணத்தில் இது முக்கியமாகப் பார்க்கப்படுகிறது.',
      nagaWhat: 'நாக தோஷம் (ராகு–கேது தோஷம்) என்றால்: ராகு அல்லது கேது லக்னத்திலிருந்து 1, 2, 7, 8-ஆம் வீடுகளில் இருப்பது. சில வட்டார மரபுகள் வேறு வீடுகளையும் சேர்க்கின்றன.',
      chevvaiLabel: 'செவ்வாய் தோஷம்', nagaLabel: 'நாக தோஷம் (ராகு–கேது)',
      state: { yes: 'உண்டு', no: 'இல்லை', cancelled: 'நிவர்த்தி' },
      spot: (n, ref) => `${ref === 'lagna' ? 'லக்னத்திலிருந்து' : 'சந்திரனிலிருந்து'} ${n}-ஆம் வீட்டில்`,
      and: ', ',
      chevvaiYes: spots => `செவ்வாய் ${spots} இருக்கிறது → செவ்வாய் தோஷம் உண்டு.`,
      chevvaiCancelled: (spots, why) => `செவ்வாய் ${spots} இருக்கிறது; ஆனால் ${why} என்பதால் தோஷம் நீங்குகிறது → தோஷம் இல்லை எனக் கொள்ளலாம்.`,
      chevvaiNo: c => `செவ்வாய் லக்னத்திலிருந்து ${c.fromLagna}-ஆம் வீட்டிலும் சந்திரனிலிருந்து ${c.fromMoon}-ஆம் வீட்டிலும் உள்ளது; இவை தோஷ வீடுகள் அல்ல → செவ்வாய் தோஷம் இல்லை.`,
      nagaYes: r => `லக்னத்திலிருந்து ராகு ${r.rahuHouse}-ஆம் வீட்டிலும் கேது ${r.ketuHouse}-ஆம் வீட்டிலும் உள்ளன → நாக தோஷம் உண்டு.`,
      nagaNo: r => `லக்னத்திலிருந்து ராகு ${r.rahuHouse}-ஆம் வீட்டிலும் கேது ${r.ketuHouse}-ஆம் வீட்டிலும் உள்ளன; இவை தோஷ வீடுகள் அல்ல → நாக தோஷம் இல்லை.`,
      both: label => `${label} இருவருக்கும் உண்டு. ஒருவரின் தோஷத்தை மற்றவரின் தோஷம் சமன் செய்யும் (தோஷ சாம்யம்) → பொருந்தும்.`,
      neither: label => `${label} இருவருக்கும் இல்லை → பொருந்தும்.`,
      onlyOne: (label, name) => `${label} ${name} ஜாதகத்தில் மட்டும் உள்ளது. மரபுப்படி தோஷம் உள்ள ஜாதகத்துக்கு தோஷம் உள்ள ஜாதகமே சேர்க்கப்படும் → பொருந்தவில்லை. பரிகாரம் அல்லது முழு ஜாதக ஆய்வு பரிந்துரைக்கப்படுகிறது.`,
      papa: (g, b, gName, bName, ok) => `${gName}: ${g} புள்ளி, ${bName}: ${b} புள்ளி. பையனின் மொத்த தோஷ வலிமை பெண்ணுக்குச் சமமாகவோ அதிகமாகவோ இருந்தால் சமன் → ${ok ? 'பொருந்தும்.' : 'பையனுக்குக் குறைவு; பொருந்தவில்லை.'}`,
      sandhiPerson: (name, lord, date) => `${name}: ${lord} தசை ${date} முதல்`,
      sandhi: (gText, bText, months, ok) => `${gText}; ${bText}. ${ok ? `இடைவெளி சுமார் ${months} மாதம் → இருவருக்கும் ஒரே நேரத்தில் பெரிய மாற்றம் இல்லை.` : `${months} மாத இடைவெளியில் இருவருக்கும் தசை மாறுகிறது → அந்தக் காலத்தில் கூடுதல் கவனம் தேவை.`}`,
      careWord: 'கவனம்',
      checkTitle: { chevvai: 'செவ்வாய் தோஷம் — இருவருக்கும் சமமா?', rahuKetu: 'நாக தோஷம் — இருவருக்கும் சமமா?', papa: 'மொத்த தோஷ வலிமை (பாப சாம்யம்)', dasaSandhi: 'தசை மாறும் நேரம் (தசா சந்தி)' },
      quality: { good: 'நல்ல காலம்', mixed: 'கலவையான காலம்', challenging: 'சவாலான காலம்' },
      qualityNote: {
        good: lord => `இந்த ஜாதகத்தில் ${lord} நல்ல நிலையில் உள்ளதால் பொதுவாகச் சாதகமான காலம்.`,
        mixed: () => 'நன்மையும் சவாலும் கலந்த காலம்; உழைப்புக்கு ஏற்ற பலன்.',
        challenging: lord => `இந்த ஜாதகத்தில் ${lord} பலவீனமான நிலையில் உள்ளதால் பொறுமையும் கவனமும் தேவை.`
      },
      meaning: { Sun: 'பதவி, அதிகாரம், தந்தை, அரசு தொடர்பு', Moon: 'மனம், தாய், பயணம், மக்கள் தொடர்பு', Mars: 'தைரியம், நிலம்–வீடு, சகோதரர்கள்', Mercury: 'கல்வி, வியாபாரம், பேச்சுத் திறன்', Jupiter: 'செல்வம், குழந்தை, சுப காரியங்கள், நல்ல பெயர்', Venus: 'திருமணம், வாகனம், சுக வசதி, கலை', Saturn: 'கடின உழைப்பு, பொறுமை, நிலையான முன்னேற்றம்', Rahu: 'திடீர் மாற்றங்கள், வெளிநாடு / வெளியூர் தொடர்பு', Ketu: 'ஆன்மிகம், பற்றின்மை, உள் தேடல்' },
      nowTitle: lord => `இப்போது: ${lord} தசை`,
      nextTitle: lord => `அடுத்து: ${lord} தசை`,
      when: range => `காலம்: ${range}.`,
      bhuktiNow: (lord, end) => `இதற்குள் இப்போது ${lord} புத்தி — ${end} வரை.`,
      means: (lord, text) => `${lord} தசை பொதுவாகக் குறிப்பது: ${text}.`,
      timelineIntro: 'ஒருவருக்குக் கடினமான காலம் வரும்போது மற்றவருக்கு நல்ல காலம் இருந்தால், அவர் குடும்பத்தைத் தாங்கிப் பிடிப்பார் என்பது மரபு. அடுத்த 25 ஆண்டுகள்:',
      tlHead: (g, b) => ['காலம்', `${g} தசை`, `${b} தசை`, 'என்ன அர்த்தம்'],
      tl: {
        bothGood: 'இருவருக்கும் நல்ல காலம் — வீடு, முதலீடு, சுப காரியங்களுக்கு ஏற்றது.',
        bothHard: 'இருவருக்கும் சவாலான காலம் — பெரிய செலவுகளிலும் முடிவுகளிலும் நிதானம் தேவை.',
        supports: (good, hard) => `${hard} சவாலான காலத்தில் இருந்தாலும், ${good} தசை நன்றாக இருப்பதால் குடும்பத்தைத் தாங்கிப் பிடிக்கும்.`,
        oneGood: good => `${good} தசை நன்றாக உள்ளது — குடும்பத்துக்குப் பலம்.`,
        oneHard: (hard, other) => `${hard} தசை சவாலானது; ${other} ஆதரவு முக்கியம்.`,
        normal: 'சாதாரண காலம் — உழைப்புக்கு ஏற்ற பலன்.'
      },
      levels: { strong: 'நல்ல பலம்', moderate: 'சராசரி', care: 'கவனம் தேவை' },
      area: { career: 'வேலை / தொழில்', health: 'உடல்நலம்', children: 'குழந்தை பாக்கியம்', marriage: 'இல்லற வாழ்க்கை' },
      areaHouse: { career: '10-ஆம் வீட்டு (தொழில் ஸ்தானம்)', health: 'லக்ன', children: '5-ஆம் வீட்டு (புத்திர ஸ்தானம்)', marriage: '7-ஆம் வீட்டு (களத்திர ஸ்தானம்)' },
      lordAt: (title, lord, house, dig) => `${title} அதிபதி ${lord} ${house}-ஆம் வீட்டில்${dig ? ` (${dig})` : ''}.`,
      jupiterAt: (house, dig) => `குரு (புத்திர காரகன்) ${house}-ஆம் வீட்டில்${dig ? ` (${dig})` : ''}.`,
      fields: text => `ஏற்ற துறைகள்: ${text}.`,
      careerFields: { Sun: 'அரசுப் பணி, நிர்வாகம், மருத்துவம்', Moon: 'மக்கள் சேவை, உணவு, விருந்தோம்பல், பயணம்', Mars: 'பொறியியல், காவல் / ராணுவம், நிலம்–கட்டடம்', Mercury: 'வியாபாரம், கணக்கு, IT, எழுத்து', Jupiter: 'ஆசிரியர், சட்டம், நிதி, ஆலோசனை', Venus: 'கலை, வடிவமைப்பு, ஊடகம், அழகுத் துறை', Saturn: 'தொழிற்சாலை, கட்டுமானம், சேவைத் துறை' },
      areaLevel: {
        career: { strong: 'தொழில் ஸ்தானம் பலமாக உள்ளது — நிலையான வளர்ச்சி எதிர்பார்க்கலாம்.', moderate: 'தொழில் ஸ்தானம் சராசரி — உழைப்புக்கு ஏற்ற பலன்.', care: 'தொழில் ஸ்தானம் பலவீனம் — வேலை மாற்றங்கள் வரலாம்; நிதானமான திட்டமிடல் தேவை.' },
        health: { strong: 'லக்னம் பலமாக உள்ளது — பொதுவாக நல்ல உடல் வலிமை.', moderate: 'லக்னம் சராசரி — வழக்கமான கவனம் போதும்.', care: 'லக்னம் பலவீனம் — உணவு, ஓய்வு, வழக்கமான மருத்துவப் பரிசோதனையில் கூடுதல் கவனம்.' },
        children: { strong: 'மரபுப்படி குழந்தை பாக்கியத்துக்கு நல்ல அமைப்பு.', moderate: 'மரபுப்படி சராசரி அமைப்பு.', care: 'மரபுப்படி பொறுமை / பரிகாரம் சொல்லப்படும் அமைப்பு. இது மருத்துவக் கணிப்பு அல்ல.' },
        marriage: { strong: 'களத்திர ஸ்தானம் பலமாக உள்ளது — இணக்கமான இல்லறம்.', moderate: 'சராசரி — புரிதலும் மனம் விட்டுப் பேசுவதும் முக்கியம்.', care: 'களத்திர ஸ்தானம் பலவீனம் — விட்டுக்கொடுத்தலும் பொறுமையும் அவசியம்.' }
      },
      why: {
        lordHidden: house => `அதிபதி ${house}-ஆம் வீட்டில் மறைவு`,
        lordWell: 'அதிபதி கேந்திர / திரிகோண வீட்டில்',
        lordWeak: 'அதிபதி நீசம்',
        benefics: list => `சுப கிரகம் ${list} இந்த வீட்டில்`,
        malefics: list => `பாப கிரகம் ${list} இந்த வீட்டில்`,
        helpers: list => `${list} இந்த வீட்டில் — தொழிலுக்கு உந்துதல்`,
        jupiter: 'குரு பார்வை உண்டு',
        jupiterWeak: 'குரு நீசம்',
        jupiterHidden: house => `குரு ${house}-ஆம் வீட்டில் மறைவு`,
        jupiterStrong: 'குரு பலம்',
        join: list => `காரணம்: ${list.join('; ')}.`
      },
      dasaBhukti: (maha, bhukti) => (bhukti ? `${maha} தசை – ${bhukti} புத்தி` : `${maha} தசை முழுவதும்`),
      period: {
        career: (span, range) => `முன்னேற்றம் எதிர்பார்க்கும் காலம்: ${span} (${range}).`,
        children: (span, range) => `மரபுப்படி சாதகமான காலம்: ${span} (${range}).`
      },
      careNote: 'உடல்நலம், குழந்தை பாக்கியம் பற்றியவை பாரம்பரிய ஜோதிடக் குறிப்புகள் மட்டுமே; மருத்துவ ஆலோசனைக்கு மாற்று அல்ல.',
      starAlert: 'பிறந்த நேரம் பற்றிய கவனம்',
      summaryStars: (n, level) => `நட்சத்திரப் பொருத்தம்: ${n}/12 (${level}).`,
      summaryNow: text => `இப்போதைய காலம்: ${text}`
    },
    en: {
      verdict: { high: 'Good match', medium: 'Compatible — a few points need attention', low: 'Decide carefully — significant concerns' },
      verdictDetail: (stars, kattam) => `Nakshatra porutham ${stars}/12 · Kattam porutham ${kattam}/4`,
      sections: { dosha: '1. Is there a dosha?', together: '2. Do the two charts match?', dasa: '3. Current and next dasa', timeline: '4. Both dasas side by side', life: '5. Future life', summary: '6. In short', expert: 'Full details for astrologers — charts, planets, calculations' },
      chevvaiWhat: 'Chevvai (Mars) dosha means Mars sits in the 2nd, 4th, 7th, 8th or 12th house from the Lagna or the Moon. The 7th house represents the spouse, so this is given weight in marriage matching.',
      nagaWhat: 'Naga (Rahu–Ketu) dosha means Rahu or Ketu sits in the 1st, 2nd, 7th or 8th house from the Lagna. Some regional traditions add other houses.',
      chevvaiLabel: 'Chevvai dosha', nagaLabel: 'Naga dosha (Rahu–Ketu)',
      state: { yes: 'Present', no: 'Absent', cancelled: 'Cancelled' },
      spot: (n, ref) => `${ordinal(n)} house from the ${ref === 'lagna' ? 'Lagna' : 'Moon'}`,
      and: ' and the ',
      chevvaiYes: spots => `Mars is in the ${spots} → Chevvai dosha is present.`,
      chevvaiCancelled: (spots, why) => `Mars is in the ${spots}, but it is cancelled because: ${why} → treated as no dosha.`,
      chevvaiNo: c => `Mars is in the ${ordinal(c.fromLagna)} house from the Lagna and the ${ordinal(c.fromMoon)} from the Moon; these are not dosha houses → no Chevvai dosha.`,
      nagaYes: r => `From the Lagna, Rahu is in the ${ordinal(r.rahuHouse)} house and Ketu in the ${ordinal(r.ketuHouse)} → Naga dosha is present.`,
      nagaNo: r => `From the Lagna, Rahu is in the ${ordinal(r.rahuHouse)} house and Ketu in the ${ordinal(r.ketuHouse)}; these are not dosha houses → no Naga dosha.`,
      both: label => `Both have ${label}. Each balances the other (dosha samyam) → matches.`,
      neither: label => `Neither has ${label} → matches.`,
      onlyOne: (label, name) => `Only ${name} has ${label}. Tradition pairs a dosha chart with another dosha chart → does not match. A remedy or full chart review is recommended.`,
      papa: (g, b, gName, bName, ok) => `${gName}: ${g} points, ${bName}: ${b} points. Balanced when the groom’s total is equal to or more than the bride’s → ${ok ? 'matches.' : 'the groom’s is lower; does not match.'}`,
      sandhiPerson: (name, lord, date) => `${name}: ${lord} dasa from ${date}`,
      sandhi: (gText, bText, months, ok) => `${gText}; ${bText}. ${ok ? `About ${months} months apart → no major change at the same time.` : `Both change within ${months} months → extra care is advised during that time.`}`,
      careWord: 'Take care',
      checkTitle: { chevvai: 'Chevvai dosha — balanced?', rahuKetu: 'Naga dosha — balanced?', papa: 'Total dosha strength (papa samyam)', dasaSandhi: 'Dasa change timing (dasa sandhi)' },
      quality: { good: 'Good period', mixed: 'Mixed period', challenging: 'Challenging period' },
      qualityNote: {
        good: lord => `${lord} is well placed in this chart, so this is generally a favourable period.`,
        mixed: () => 'A mix of gains and challenges; results follow effort.',
        challenging: lord => `${lord} is weak in this chart, so patience and care are needed.`
      },
      meaning: { Sun: 'status, authority, father, government links', Moon: 'mind, mother, travel, public contact', Mars: 'courage, land and property, siblings', Mercury: 'education, business, communication', Jupiter: 'wealth, children, auspicious events, reputation', Venus: 'marriage, vehicles, comforts, arts', Saturn: 'hard work, patience, steady progress', Rahu: 'sudden changes, foreign or distant links', Ketu: 'spirituality, detachment, inner search' },
      nowTitle: lord => `Now: ${lord} dasa`,
      nextTitle: lord => `Next: ${lord} dasa`,
      when: range => `Period: ${range}.`,
      bhuktiNow: (lord, end) => `Within it, ${lord} bhukti runs until ${end}.`,
      means: (lord, text) => `${lord} dasa generally signifies: ${text}.`,
      timelineIntro: 'Tradition holds that when one partner is in a difficult period and the other is in a good one, the stronger partner carries the family. The next 25 years:',
      tlHead: (g, b) => ['Period', `${g} dasa`, `${b} dasa`, 'What it means'],
      tl: {
        bothGood: 'A good period for both — suited to a home, investments and celebrations.',
        bothHard: 'A challenging period for both — be cautious with big expenses and decisions.',
        supports: (good, hard) => `${hard} is in a challenging period, but ${good}’s good dasa supports the family.`,
        oneGood: good => `${good}’s dasa is good — a strength for the family.`,
        oneHard: (hard, other) => `${hard}’s dasa is challenging; ${other}’s support matters.`,
        normal: 'An ordinary period — results follow effort.'
      },
      levels: { strong: 'Strong', moderate: 'Average', care: 'Needs care' },
      area: { career: 'Work / career', health: 'Health', children: 'Children', marriage: 'Married life' },
      areaHouse: { career: '10th-house (career)', health: 'Lagna', children: '5th-house (children)', marriage: '7th-house (spouse)' },
      lordAt: (title, lord, house, dig) => `The ${title} lord ${lord} is in the ${ordinal(house)} house${dig ? ` (${dig})` : ''}.`,
      jupiterAt: (house, dig) => `Jupiter (significator of children) is in the ${ordinal(house)} house${dig ? ` (${dig})` : ''}.`,
      fields: text => `Suitable fields: ${text}.`,
      careerFields: { Sun: 'government, administration, medicine', Moon: 'public service, food, hospitality, travel', Mars: 'engineering, police / defence, real estate', Mercury: 'business, accounts, IT, writing', Jupiter: 'teaching, law, finance, advisory', Venus: 'arts, design, media, beauty', Saturn: 'industry, construction, service sector' },
      areaLevel: {
        career: { strong: 'The career house is strong — steady growth can be expected.', moderate: 'The career house is average — results follow effort.', care: 'The career house is weak — job changes may come; plan carefully.' },
        health: { strong: 'The Lagna is strong — generally good vitality.', moderate: 'The Lagna is average — routine care is enough.', care: 'The Lagna is weak — extra attention to diet, rest and regular check-ups.' },
        children: { strong: 'Traditionally a good indication for children.', moderate: 'Traditionally an average indication.', care: 'Traditionally an indication where patience or remedies are suggested. This is not a medical prediction.' },
        marriage: { strong: 'The spouse house is strong — a harmonious married life.', moderate: 'Average — understanding and open conversation matter.', care: 'The spouse house is weak — mutual adjustment and patience are essential.' }
      },
      why: {
        lordHidden: house => `its lord is hidden in the ${ordinal(house)} house`,
        lordWell: 'its lord is in a kendra / trikona house',
        lordWeak: 'its lord is debilitated',
        benefics: list => `benefic ${list} in this house`,
        malefics: list => `malefic ${list} in this house`,
        helpers: list => `${list} in this house drives the career`,
        jupiter: 'aspected by Jupiter',
        jupiterWeak: 'Jupiter is debilitated',
        jupiterHidden: house => `Jupiter is hidden in the ${ordinal(house)} house`,
        jupiterStrong: 'Jupiter is strong',
        join: list => `Why: ${list.join('; ')}.`
      },
      dasaBhukti: (maha, bhukti) => (bhukti ? `${maha} dasa – ${bhukti} bhukti` : `the whole ${maha} dasa`),
      period: {
        career: (span, range) => `Expected period of progress: ${span} (${range}).`,
        children: (span, range) => `Traditionally favourable period: ${span} (${range}).`
      },
      careNote: 'Notes on health and children are traditional astrological indications only, not a substitute for medical advice.',
      starAlert: 'Check the birth time',
      summaryStars: (n, level) => `Nakshatra porutham: ${n}/12 (${level}).`,
      summaryNow: text => `Current period: ${text}`
    }
  };

  function timelineNote(p, row, names) {
    const groom = row.groom ? row.groom.quality : 'mixed';
    const bride = row.bride ? row.bride.quality : 'mixed';
    if (groom === 'good' && bride === 'good') return p.tl.bothGood;
    if (groom === 'challenging' && bride === 'challenging') return p.tl.bothHard;
    const good = groom === 'good' ? names.groom : bride === 'good' ? names.bride : null;
    const hard = groom === 'challenging' ? names.groom : bride === 'challenging' ? names.bride : null;
    if (good && hard) return p.tl.supports(good, hard);
    if (good) return p.tl.oneGood(good);
    if (hard) return p.tl.oneHard(hard, hard === names.groom ? names.bride : names.groom);
    return p.tl.normal;
  }

  function plainSections(report, ctx) {
    const { analysis, porutham, finalLevel, roles, w, p, formatMonth, alerts, yearMs } = ctx;
    const lines = [];
    const nameOf = Object.fromEntries(roles);
    const planet = key => w.planets[key];
    const range = period => `${formatMonth(period.start)} – ${formatMonth(period.end)}`;
    const heading = text => { report.append(el('h3', text, 'kattam-heading')); lines.push('', `== ${text} ==`); };
    const person = name => { report.append(el('h4', name, 'kattam-person')); lines.push(`-- ${name} --`); };
    const note = (text, className = 'kattam-note') => { report.append(el('p', text, className)); lines.push(text); };
    const list = () => { const node = el('ul', undefined, 'match-results'); report.append(node); return node; };
    const item = (target, title, tone, badge, paragraphs) => {
      const texts = paragraphs.filter(Boolean);
      const li = el('li', undefined, `match-result tone-${tone}`);
      li.append(el('strong', title), el('span', badge, 'match-status'));
      texts.forEach(text => li.append(el('p', text)));
      target.append(li);
      lines.push(`${title} — ${badge}`, ...texts.map(text => `   ${text}`));
    };

    if (alerts.length) {
      const box = el('div', undefined, 'notice');
      box.append(el('strong', p.starAlert));
      alerts.forEach(text => box.append(el('p', text)));
      report.append(box);
      lines.push(p.starAlert, ...alerts);
    }

    heading(p.sections.dosha);
    note(p.chevvaiWhat);
    note(p.nagaWhat);
    const states = {};
    for (const [role, name] of roles) {
      const { chevvai: c, rahuKetu } = analysis[role];
      const spots = [['lagna', c.fromLagna], ['moon', c.fromMoon]]
        .filter(([, house]) => CHEVVAI_HOUSES.includes(house))
        .map(([ref, house]) => p.spot(house, ref)).join(p.and);
      const chevvai = !c.raw ? ['no', p.chevvaiNo(c)]
        : c.cancellations.length ? ['cancelled', p.chevvaiCancelled(spots, c.cancellations.map(reason => w.cancel[reason]).join(', '))]
          : ['yes', p.chevvaiYes(spots)];
      const naga = rahuKetu.dosha ? ['yes', p.nagaYes(rahuKetu)] : ['no', p.nagaNo(rahuKetu)];
      states[role] = { chevvai: chevvai[0], naga: naga[0] };
      person(name);
      const target = list();
      item(target, p.chevvaiLabel, TONES[chevvai[0]], p.state[chevvai[0]], [chevvai[1]]);
      item(target, p.nagaLabel, TONES[naga[0]], p.state[naga[0]], [naga[1]]);
    }

    heading(p.sections.together);
    const together = list();
    for (const check of analysis.checks) {
      let text;
      if (check.key === 'chevvai' || check.key === 'rahuKetu') {
        const key = check.key === 'chevvai' ? 'chevvai' : 'naga';
        const label = key === 'chevvai' ? p.chevvaiLabel : p.nagaLabel;
        const has = roles.filter(([role]) => states[role][key] === 'yes');
        text = has.length === 2 ? p.both(label) : has.length === 0 ? p.neither(label) : p.onlyOne(label, has[0][1]);
      } else if (check.key === 'papa') {
        text = p.papa(analysis.groom.papa.total, analysis.bride.papa.total, nameOf.groom, nameOf.bride, check.ok);
      } else {
        const label = role => {
          const next = analysis[role].dasa.next;
          return next ? p.sandhiPerson(nameOf[role], planet(next.lord), formatMonth(next.start)) : `${nameOf[role]}: —`;
        };
        text = p.sandhi(label('groom'), label('bride'), Number.isFinite(check.gapMs) ? Math.round(check.gapMs / (yearMs / 12)) : '—', check.ok);
      }
      const badge = check.ok ? w.ok : check.key === 'dasaSandhi' ? p.careWord : w.notOk;
      item(together, p.checkTitle[check.key], check.ok ? 'good' : 'care', badge, [text]);
    }

    heading(p.sections.dasa);
    for (const [role, name] of roles) {
      const dasa = analysis[role].dasa;
      person(name);
      const target = list();
      if (dasa.current) {
        const lord = planet(dasa.current.lord);
        item(target, p.nowTitle(lord), TONES[dasa.current.quality], p.quality[dasa.current.quality], [
          p.when(range(dasa.current)),
          dasa.currentBhukti && p.bhuktiNow(planet(dasa.currentBhukti.lord), formatMonth(dasa.currentBhukti.end)),
          p.means(lord, p.meaning[dasa.current.lord]),
          p.qualityNote[dasa.current.quality](lord)
        ]);
      }
      if (dasa.next) {
        const lord = planet(dasa.next.lord);
        item(target, p.nextTitle(lord), TONES[dasa.next.quality], p.quality[dasa.next.quality], [
          p.when(range(dasa.next)), p.means(lord, p.meaning[dasa.next.lord]), p.qualityNote[dasa.next.quality](lord)
        ]);
      }
    }

    heading(p.sections.timeline);
    note(p.timelineIntro);
    const timeline = el('table', undefined, 'match-profile kattam-table kattam-timeline');
    const headRow = el('tr');
    p.tlHead(nameOf.groom, nameOf.bride).forEach(text => { const cell = el('th', text); cell.scope = 'col'; headRow.append(cell); });
    const thead = el('thead');
    thead.append(headRow);
    const tbody = el('tbody');
    const dasaCell = period => {
      const cell = el('td', period ? `${planet(period.lord)} — ${p.quality[period.quality]}` : '—');
      if (period) cell.className = `tone-${TONES[period.quality]}`;
      return cell;
    };
    for (const row of analysis.timeline) {
      const tr = el('tr');
      const when = el('th', range(row));
      when.scope = 'row';
      const meaning = timelineNote(p, row, nameOf);
      tr.append(when, dasaCell(row.groom), dasaCell(row.bride), el('td', meaning));
      tbody.append(tr);
      const describe = period => (period ? `${planet(period.lord)} (${p.quality[period.quality]})` : '—');
      lines.push(`${range(row)}: ${nameOf.groom} ${describe(row.groom)} | ${nameOf.bride} ${describe(row.bride)} — ${meaning}`);
    }
    timeline.append(thead, tbody);
    const scroller = el('div', undefined, 'kattam-table-scroll');
    scroller.append(timeline);
    report.append(scroller);

    const reasonsFor = (area, info) => {
      const reasons = [];
      if (HIDDEN_HOUSES.includes(info.lordHouse)) reasons.push(p.why.lordHidden(info.lordHouse));
      else if (WELL_PLACED_HOUSES.includes(info.lordHouse)) reasons.push(p.why.lordWell);
      if (info.lordDignity === 'debilitated') reasons.push(p.why.lordWeak);
      if (info.benefics.length) reasons.push(p.why.benefics(info.benefics.map(planet).join(', ')));
      const helpers = area === 'career' ? info.malefics.filter(key => key === 'Sun' || key === 'Mars') : [];
      if (helpers.length) reasons.push(p.why.helpers(helpers.map(planet).join(', ')));
      if (area !== 'career' && info.malefics.length) reasons.push(p.why.malefics(info.malefics.map(planet).join(', ')));
      if (info.jupiterAspect) reasons.push(p.why.jupiter);
      if (area === 'children') {
        if (info.jupiterDignity === 'debilitated') reasons.push(p.why.jupiterWeak);
        else if (HIDDEN_HOUSES.includes(info.jupiterHouse)) reasons.push(p.why.jupiterHidden(info.jupiterHouse));
        else if (info.jupiterDignity) reasons.push(p.why.jupiterStrong);
      }
      return reasons.length ? p.why.join(reasons) : '';
    };

    heading(p.sections.life);
    for (const [role, name] of roles) {
      const life = analysis[role].life;
      person(name);
      const target = list();
      for (const area of ['career', 'health', 'children', 'marriage']) {
        const info = life[area];
        const parts = [p.lordAt(p.areaHouse[area], planet(info.lord), info.lordHouse, info.lordDignity && w.dignity[info.lordDignity])];
        if (area === 'career') parts.push(p.fields(p.careerFields[info.lord]));
        if (area === 'children') parts.push(p.jupiterAt(info.jupiterHouse, info.jupiterDignity && w.dignity[info.jupiterDignity]));
        parts.push(p.areaLevel[area][info.level], reasonsFor(area, info));
        if (info.period) parts.push(p.period[area](p.dasaBhukti(planet(info.period.maha), info.period.bhukti && planet(info.period.bhukti)), range(info.period)));
        item(target, p.area[area], TONES[info.level], p.levels[info.level], parts);
      }
    }
    note(p.careNote, 'form-help');

    heading(p.sections.summary);
    const summary = [
      p.summaryStars(porutham.matchedCount, w.poruthamLevels[porutham.level]),
      ...analysis.checks.map(check => (check.ok ? w.summaryOk : w.summaryBad)[check.key]),
      analysis.timeline.length ? p.summaryNow(timelineNote(p, analysis.timeline[0], nameOf)) : '',
      { high: w.finalHigh, medium: w.finalMedium, low: w.finalLow }[finalLevel]
    ].filter(Boolean);
    const box = el('div', undefined, `kattam-summary level-${finalLevel}`);
    summary.forEach(sentence => box.append(el('p', sentence)));
    report.append(box);
    lines.push(...summary);
    return lines;
  }

  const el = (tag, content, className) => {
    const node = document.createElement(tag);
    if (content !== undefined) node.textContent = content;
    if (className) node.className = className;
    return node;
  };
  const formatDegree = value => `${Math.floor(value)}°${String(Math.floor((value % 1) * 60)).padStart(2, '0')}′`;

  function chartCells(chart, kind) {
    const cells = Array.from({ length: 12 }, () => []);
    cells[kind === 'rasi' ? chart.lagna.sign : chart.lagna.navamsa].push({ key: 'Lagna', retrograde: false });
    for (const [planet, place] of Object.entries(chart.planets)) {
      cells[kind === 'rasi' ? place.sign : place.navamsa].push({ key: planet, retrograde: place.retrograde && planet !== 'Rahu' && planet !== 'Ketu' });
    }
    return cells;
  }

  function chartGrid(chart, kind, owner, w, names) {
    const cells = chartCells(chart, kind);
    const grid = el('div', undefined, 'kattam-grid');
    const summary = [];
    cells.forEach((occupants, sign) => {
      const cell = el('div', undefined, 'kattam-cell');
      const [row, column] = SOUTH_INDIAN_CELLS[sign];
      cell.style.gridRow = String(row);
      cell.style.gridColumn = String(column);
      cell.append(el('small', names.rasi[sign], 'kattam-sign'));
      const labels = occupants.map(item => `${w.short[item.key]}${item.retrograde ? `(${w.retro})` : ''}`);
      if (occupants.some(item => item.key === 'Lagna')) cell.classList.add('is-lagna');
      if (labels.length) {
        cell.append(el('span', labels.join(' '), 'kattam-planets'));
        summary.push(`${names.rasi[sign]}: ${labels.join(', ')}`);
      }
      grid.append(cell);
    });
    const center = el('div', undefined, 'kattam-center');
    center.append(el('strong', owner), el('span', kind === 'rasi' ? w.rasiChart : w.navamsaChart));
    grid.append(center);
    grid.setAttribute('role', 'img');
    grid.setAttribute('aria-label', `${owner} ${kind === 'rasi' ? w.rasiChart : w.navamsaChart}: ${summary.join('; ')}`);
    return { grid, summary };
  }

  function table(headings, rows, caption) {
    const node = el('table', undefined, 'match-profile kattam-table');
    if (caption) node.append(el('caption', caption));
    const head = el('tr');
    headings.forEach(heading => { const cell = el('th', heading); cell.scope = 'col'; head.append(cell); });
    const thead = el('thead');
    thead.append(head);
    const body = el('tbody');
    rows.forEach(values => {
      const row = el('tr');
      values.forEach((value, index) => {
        const cell = el(index === 0 ? 'th' : 'td', value);
        if (index === 0) cell.scope = 'row';
        row.append(cell);
      });
      body.append(row);
    });
    node.append(thead, body);
    const scroller = el('div', undefined, 'kattam-table-scroll');
    scroller.append(node);
    return scroller;
  }

  function build(options) {
    const { charts, people, selected, language, nowMs } = options;
    const w = WORDS[language] || WORDS.ta;
    const names = { rasi: options.rasis, star: options.nakshatras };
    const engine = root.JathagamEngine;
    const analysis = engine.analysePair(charts.bride, charts.groom, nowMs);
    const dateFormat = new Intl.DateTimeFormat(language === 'en' ? 'en-GB' : 'ta-IN', { day: 'numeric', month: 'short', year: 'numeric' });
    const formatDate = ms => dateFormat.format(new Date(ms));
    const roles = [['groom', people.groom.name || w.groom], ['bride', people.bride.name || w.bride]];
    const starName = place => `${names.star[place.star]} (${place.pada})`;
    const p = PLAIN[language] || PLAIN.ta;
    const monthFormat = new Intl.DateTimeFormat(language === 'en' ? 'en-GB' : 'ta-IN', { month: 'short', year: 'numeric' });
    const formatMonth = ms => monthFormat.format(new Date(ms));
    const header = [w.title, `${roles[0][1]} · ${roles[1][1]}`, ''];
    const lines = [];
    const report = el('article', undefined, 'kattam-report');

    const computedStars = { bride: charts.bride.planets.Moon, groom: charts.groom.planets.Moon };
    const porutham = root.PoruthamRules.calculate(computedStars.bride.star, computedStars.groom.star, computedStars.bride.sign, computedStars.groom.sign);
    const ranks = { low: 0, medium: 1, high: 2 };
    const finalLevel = ['low', 'medium', 'high'][Math.min(ranks[porutham.level], ranks[analysis.level])];

    const verdict = el('div', undefined, `match-verdict level-${finalLevel}`);
    verdict.setAttribute('role', 'status');
    const verdictDetail = `${p.verdictDetail(porutham.matchedCount, 4 - analysis.failures)} · ${roles[0][1]} · ${roles[1][1]}`;
    verdict.append(el('strong', p.verdict[finalLevel]), el('span', verdictDetail));
    report.append(verdict);
    header.push(p.verdict[finalLevel], verdictDetail);

    const starNotes = [];
    const alerts = [];
    for (const [role, name] of roles) {
      const computed = computedStars[role];
      const chosen = selected && selected[role];
      if (chosen && chosen.nakshatra !== '' && chosen.nakshatra !== undefined) {
        if (Number(chosen.nakshatra) === computed.star && Number(chosen.rasi) === computed.sign) {
          starNotes.push(w.starSame(name, names.star[computed.star]));
        } else {
          const text = w.starDiff(name, `${names.rasi[chosen.rasi]} / ${names.star[chosen.nakshatra]}`, `${names.rasi[computed.sign]} / ${names.star[computed.star]}`);
          starNotes.push(text);
          alerts.push(text);
        }
      } else {
        starNotes.push(w.starComputed(name, names.star[computed.star]));
      }
      const starFraction = (computed.longitude * 27 / 360) % 1;
      const edges = [];
      if (starFraction < 0.02 || starFraction > 0.98) edges.push(w.edgeMoon(name));
      if (charts[role].lagna.degree < 1 || charts[role].lagna.degree > 29) edges.push(w.edgeLagna(name));
      starNotes.push(...edges);
      alerts.push(...edges);
    }
    starNotes.push(w.poruthamScore(porutham.matchedCount, w.poruthamLevels[porutham.level]));

    const plainLines = plainSections(report, { analysis, porutham, finalLevel, roles, w, p, formatMonth, alerts, yearMs: engine.YEAR_MS });

    const details = el('details', undefined, 'kattam-expert');
    details.append(el('summary', p.sections.expert));
    const node = el('div', undefined, 'kattam-expert-body');
    details.append(node);
    report.append(details);

    const section = (key) => {
      node.append(el('h3', w.sections[key], 'kattam-heading'));
      lines.push('', `== ${w.sections[key]} ==`);
    };

    section('birth');
    const birthRows = [
      [w.rows.date, ...roles.map(([role]) => people[role].birth_date)],
      [w.rows.time, ...roles.map(([role]) => people[role].birth_time)],
      [w.rows.place, ...roles.map(([role]) => people[role].place)],
      [w.rows.coordinates, ...roles.map(([role]) => `${people[role].latitude}, ${people[role].longitude}`)],
      [w.rows.timezone, ...roles.map(([role]) => people[role].timezone)],
      [w.rows.lagna, ...roles.map(([role]) => `${names.rasi[charts[role].lagna.sign]} ${formatDegree(charts[role].lagna.degree)}`)],
      [w.rows.rasi, ...roles.map(([role]) => names.rasi[computedStars[role].sign])],
      [w.rows.star, ...roles.map(([role]) => starName(computedStars[role]))],
      [w.rows.ayanamsa, ...roles.map(([role]) => formatDegree(charts[role].ayanamsa))]
    ];
    node.append(table(['', roles[0][1], roles[1][1]], birthRows));
    birthRows.forEach(([label, first, second]) => lines.push(`${label}: ${first} | ${second}`));

    section('charts');
    const chartWrap = el('div', undefined, 'kattam-charts');
    for (const [role, name] of roles) {
      for (const kind of ['rasi', 'navamsa']) {
        const figure = el('figure', undefined, 'kattam-figure');
        const { grid, summary } = chartGrid(charts[role], kind, name, w, names);
        figure.append(grid, el('figcaption', `${name} — ${kind === 'rasi' ? w.rasiChart : w.navamsaChart}`));
        chartWrap.append(figure);
        lines.push(`${name} ${kind === 'rasi' ? w.rasiChart : w.navamsaChart}: ${summary.join(' | ')}`);
      }
    }
    node.append(chartWrap);

    section('planets');
    for (const [role, name] of roles) {
      const chart = charts[role];
      const rows = [[w.lagna, names.rasi[chart.lagna.sign], formatDegree(chart.lagna.degree), starName(chart.lagna), names.rasi[chart.lagna.navamsa], '']];
      for (const planet of engine.PLANET_ORDER) {
        const place = chart.planets[planet];
        const status = [engine.dignity(planet, place.sign) && w.dignity[engine.dignity(planet, place.sign)], place.retrograde && planet !== 'Rahu' && planet !== 'Ketu' ? `${w.retro}` : ''].filter(Boolean).join(', ');
        rows.push([w.planets[planet], names.rasi[place.sign], formatDegree(place.degree), starName(place), names.rasi[place.navamsa], status]);
      }
      node.append(table(w.planetHead, rows, name));
      lines.push(`-- ${name} --`);
      rows.forEach(row => lines.push(row.filter(Boolean).join(' | ')));
    }

    section('checks');
    const list = el('ol', undefined, 'match-results');
    const months = ms => Math.round(ms / (engine.YEAR_MS / 12));
    for (const check of analysis.checks) {
      const parts = [];
      if (check.key === 'chevvai') {
        roles.forEach(([role, name]) => parts.push(`${name}: ${w.chevvaiPerson(analysis[role].chevvai, w)}`));
        parts.push(w.chevvaiRule);
      } else if (check.key === 'rahuKetu') {
        roles.forEach(([role, name]) => parts.push(`${name}: ${w.rahuPerson(analysis[role].rahuKetu, w)}`));
        parts.push(w.rahuRule);
      } else if (check.key === 'papa') {
        parts.push(w.papaRule(analysis.bride.papa.total, analysis.groom.papa.total));
        roles.forEach(([role, name]) => {
          const grouped = Object.keys(w.papaRefs).map(reference => {
            const hits = analysis[role].papa.hits.filter(hit => hit.reference === reference);
            return `${w.papaRefs[reference]}: ${hits.length ? hits.map(hit => `${w.planets[hit.planet]} (${hit.house})`).join(', ') : w.none}`;
          });
          parts.push(`${name} — ${grouped.join('; ')}`);
        });
      } else {
        const next = role => analysis[role].dasa.next;
        const label = role => next(role) ? `${w.dasaName(w.planets[next(role).lord])} ${formatDate(next(role).start)}` : w.none;
        parts.push(w.dasaRule(label('bride'), label('groom'), Number.isFinite(check.gapMs) ? months(check.gapMs) : '—'));
      }
      const item = el('li', undefined, `match-result ${check.ok ? 'is-match' : 'no-match'}`);
      item.append(el('strong', w.checks[check.key]), el('span', check.ok ? w.ok : w.notOk, 'match-status'));
      parts.forEach(part => item.append(el('p', part)));
      list.append(item);
      lines.push(`${w.checks[check.key]} — ${check.ok ? w.ok : w.notOk}`, ...parts.map(part => `   ${part}`));
    }
    node.append(list);

    section('seventh');
    for (const [role, name] of roles) {
      const sentence = `${name}: ${w.seventh(analysis[role].seventh, w, names)}`;
      node.append(el('p', sentence, 'kattam-note'));
      lines.push(sentence);
    }

    section('dasa');
    const dasaRows = Object.keys(w.dasaRows).map(key => [w.dasaRows[key], ...roles.map(([role]) => {
      const dasa = analysis[role].dasa;
      if (key === 'birth') {
        const totalMonths = months(dasa.balanceMs);
        return `${w.dasaName(w.planets[dasa.birthLord])} (${w.balance(Math.floor(totalMonths / 12), totalMonths % 12)})`;
      }
      if (key === 'current') {
        return dasa.current ? `${w.dasaName(w.planets[dasa.current.lord])} / ${w.bhukti(w.planets[dasa.currentBhukti.lord])} (${formatDate(dasa.currentBhukti.start)} – ${formatDate(dasa.currentBhukti.end)})` : w.none;
      }
      return dasa.next ? `${w.dasaName(w.planets[dasa.next.lord])} — ${formatDate(dasa.next.start)}` : w.none;
    })]);
    node.append(table(['', roles[0][1], roles[1][1]], dasaRows));
    dasaRows.forEach(([label, bride, groom]) => lines.push(`${label}: ${bride} | ${groom}`));

    section('star');
    starNotes.forEach(note => node.append(el('p', note, 'kattam-note')));
    lines.push(...starNotes);

    node.append(el('h3', w.sections.method, 'kattam-heading'), el('p', w.method, 'form-help'));
    lines.push('', `== ${w.sections.method} ==`, w.method);
    report.append(el('p', w.disclaimer, 'form-help kattam-disclaimer'));

    const text = [...header, ...plainLines, '', '', `==== ${p.sections.expert} ====`, ...lines, '', w.disclaimer].join('\n');
    return { node: report, text, title: w.title, analysis, finalLevel };
  }

  if (typeof root.addEventListener === 'function') {
    root.addEventListener('beforeprint', () => {
      root.document.querySelectorAll('details.kattam-expert').forEach(details => { details.open = true; });
    });
  }

  root.KattamReport = Object.freeze({ build });
})(typeof globalThis !== 'undefined' ? globalThis : this);
