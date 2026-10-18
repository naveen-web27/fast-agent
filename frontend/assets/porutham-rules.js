// Mirrors backend/app/features/ai_reports/rules.py; backend/tests/test_porutham_parity.py checks they agree.
(function (root) {
  'use strict';

  const GANA = ['deva', 'manushya', 'rakshasa', 'manushya', 'deva', 'manushya', 'deva', 'deva', 'rakshasa',
    'rakshasa', 'manushya', 'manushya', 'deva', 'rakshasa', 'deva', 'rakshasa', 'deva', 'rakshasa',
    'rakshasa', 'manushya', 'manushya', 'deva', 'rakshasa', 'rakshasa', 'manushya', 'manushya', 'deva'];
  const YONI = ['horse', 'elephant', 'sheep', 'snake', 'snake', 'dog', 'cat', 'sheep', 'cat',
    'rat', 'rat', 'cow', 'buffalo', 'tiger', 'buffalo', 'tiger', 'deer', 'deer',
    'dog', 'monkey', 'mongoose', 'monkey', 'lion', 'horse', 'lion', 'cow', 'elephant'];
  const YONI_ENEMY = { horse: 'buffalo', buffalo: 'horse', elephant: 'lion', lion: 'elephant', sheep: 'monkey', monkey: 'sheep',
    snake: 'mongoose', mongoose: 'snake', dog: 'deer', deer: 'dog', cat: 'rat', rat: 'cat', cow: 'tiger', tiger: 'cow' };
  const RAJJU = ['foot', 'thigh', 'navel', 'neck', 'head', 'neck', 'navel', 'thigh', 'foot',
    'foot', 'thigh', 'navel', 'neck', 'head', 'neck', 'navel', 'thigh', 'foot',
    'foot', 'thigh', 'navel', 'neck', 'head', 'neck', 'navel', 'thigh', 'foot'];
  const VEDHA_GROUPS = [[0, 17], [1, 16], [2, 15], [3, 14], [5, 21], [6, 20], [7, 19], [8, 18],
    [9, 26], [10, 25], [11, 24], [12, 23], [4, 13, 22]];
  const SIGN_LORDS = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter'];
  const FRIENDS = { Sun: ['Moon', 'Mars', 'Jupiter'], Moon: ['Sun', 'Mercury'], Mars: ['Sun', 'Moon', 'Jupiter'],
    Mercury: ['Sun', 'Venus'], Jupiter: ['Sun', 'Moon', 'Mars'], Venus: ['Mercury', 'Saturn'], Saturn: ['Mercury', 'Venus'] };
  const ENEMIES = { Sun: ['Venus', 'Saturn'], Moon: [], Mars: ['Mercury'], Mercury: ['Moon'],
    Jupiter: ['Mercury', 'Venus'], Venus: ['Sun', 'Moon'], Saturn: ['Sun', 'Moon', 'Mars'] };
  const VASIYA = [[4, 7], [3, 6], [5], [7, 8], [6], [2, 11], [5, 9], [3], [11], [10], [9], [9]];
  const DINA_REMAINDERS = [0, 2, 4, 6, 8];
  const MAHENDRA_COUNTS = [4, 7, 10, 13, 16, 19, 22, 25];
  const RASI_COUNTS = [1, 3, 4, 7, 10, 11];
  const NADI_CYCLE = ['adi', 'madhya', 'antya', 'antya', 'madhya', 'adi'];
  const VARNA = ['kshatriya', 'vaishya', 'shudra', 'brahmin', 'kshatriya', 'vaishya',
    'shudra', 'brahmin', 'kshatriya', 'vaishya', 'shudra', 'brahmin'];
  const VARNA_RANK = { shudra: 0, vaishya: 1, kshatriya: 2, brahmin: 3 };

  const nadi = star => NADI_CYCLE[star % 6];

  // Each Rasi spans nine padas; returns the stars (and their padas) that fall inside it.
  function starsForRasi(rasi) {
    const stars = [];
    for (let star = 0; star < 27; star += 1) {
      const padas = [0, 1, 2, 3].filter(pada => Math.floor((star * 4 + pada) / 9) === rasi).map(pada => pada + 1);
      if (padas.length) stars.push({ star, padas });
    }
    return stars;
  }

  function calculate(brideStar, groomStar, brideRasi, groomRasi) {
    for (const [value, ceiling] of [[brideStar, 27], [groomStar, 27], [brideRasi, 12], [groomRasi, 12]]) {
      if (!Number.isInteger(value) || value < 0 || value >= ceiling) throw new RangeError('Star or Rasi index out of range');
    }
    const count = ((groomStar - brideStar) % 27 + 27) % 27 + 1;
    const signCount = ((groomRasi - brideRasi) % 12 + 12) % 12 + 1;
    const brideLord = SIGN_LORDS[brideRasi];
    const groomLord = SIGN_LORDS[groomRasi];
    const lordPass = brideLord === groomLord || (!ENEMIES[brideLord].includes(groomLord) && !ENEMIES[groomLord].includes(brideLord)
      && (FRIENDS[brideLord].includes(groomLord) || FRIENDS[groomLord].includes(brideLord)));
    const ganaPass = GANA[brideStar] === GANA[groomStar] || (GANA[brideStar] !== 'rakshasa' && GANA[groomStar] !== 'rakshasa');
    const vedhaGroup = VEDHA_GROUPS.find(group => brideStar !== groomStar && group.includes(brideStar) && group.includes(groomStar));
    const checks = [
      { key: 'dina', matches: DINA_REMAINDERS.includes(count % 9), details: { count, remainder: count % 9 } },
      { key: 'gana', matches: ganaPass, details: { bride: GANA[brideStar], groom: GANA[groomStar] } },
      { key: 'mahendra', matches: MAHENDRA_COUNTS.includes(count), details: { count } },
      { key: 'stree_deergha', matches: count > 13, details: { count } },
      { key: 'yoni', matches: YONI_ENEMY[YONI[brideStar]] !== YONI[groomStar], details: { bride: YONI[brideStar], groom: YONI[groomStar], enemy: YONI_ENEMY[YONI[brideStar]] } },
      { key: 'rasi', matches: RASI_COUNTS.includes(signCount), details: { signCount } },
      { key: 'rasi_adhipathi', matches: lordPass, details: { bride: brideLord, groom: groomLord } },
      { key: 'vasiya', matches: VASIYA[brideRasi].includes(groomRasi), details: { brideTargets: VASIYA[brideRasi] } },
      { key: 'rajju', matches: RAJJU[brideStar] !== RAJJU[groomStar], details: { bride: RAJJU[brideStar], groom: RAJJU[groomStar] } },
      { key: 'vedha', matches: !vedhaGroup, details: { group: vedhaGroup || [] } },
      { key: 'nadi', matches: nadi(brideStar) !== nadi(groomStar), details: { bride: nadi(brideStar), groom: nadi(groomStar) } },
      { key: 'varna', matches: VARNA_RANK[VARNA[brideRasi]] <= VARNA_RANK[VARNA[groomRasi]], details: { bride: VARNA[brideRasi], groom: VARNA[groomRasi] } }
    ];
    const matchedCount = checks.filter(check => check.matches).length;
    const rajjuFails = !checks[8].matches;
    let level = matchedCount >= 9 ? 'high' : matchedCount >= 6 ? 'medium' : 'low';
    // Tradition treats a Rajju mismatch as serious, so it caps an otherwise high count at medium.
    if (rajjuFails && level === 'high') level = 'medium';
    return { checks, matchedCount, total: checks.length, level, rajjuFails, count, signCount };
  }

  root.PoruthamRules = Object.freeze({ calculate, starsForRasi, nadi, GANA, YONI, RAJJU, SIGN_LORDS });
})(typeof globalThis !== 'undefined' ? globalThis : this);
