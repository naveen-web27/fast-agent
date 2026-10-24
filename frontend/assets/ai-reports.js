(() => {
  'use strict';

  const API = '/api/v1/ai-reports';
  const CAPABILITY_KEY = 'rightconnect-ai-report-capabilities-v1';
  const PAID_KEY = 'rightconnect-kattam-paid-v1';
  const RAZORPAY_CHECKOUT = 'https://checkout.razorpay.com/v1/checkout.js';
  const PDF_SCRIPTS = ['/assets/vendor/html2canvas-1.4.1.min.js', '/assets/vendor/jspdf-2.5.2.umd.min.js'];
  const words = {
    ta: {
      appTitle: 'தமிழ் ஜோதிடம் & கலைகள் AI அறிக்கைகள்', eyebrow: 'பாரம்பரியக் கலைகள்',
      servicesHubTitle: 'சேவைகள்', servicesHubEyebrow: 'RightConnect சேவைகள்',
      astrologyHubTitle: 'ஜோதிடம் மற்றும் தொடர்புடைய சேவைகள்', astrologyHubEyebrow: 'பாரம்பரியக் கலைகள்',
      allServiceCategories: 'அனைத்து சேவை வகைகளும்',
      compatibilityPageTitle: 'திருமணப் பொருத்தம் & ஜாதகம்', compatibilityNav: 'பொருத்தம் & ஜாதகம்',
      compatibilityDisclaimer: 'பன்னிரண்டு பாரம்பரிய விதிகள் ஒப்பிடப்படுகின்றன. இவை அறிவியல் கணிப்போ திருமண வெற்றியின் சதவீதமோ அல்ல. வர்ணம் ஒரு வரலாற்று, சாதி சார்ந்த வகைப்பாடு; இது யாருடைய மதிப்பையும் தீர்மானிக்காது.',
      backToRasi: 'ராசி முடிவுகளுக்குத் திரும்பு',
      rasiStepTitle: 'ராசி பொருத்தம்', rasiStepHelp: 'மணமகள், மணமகனின் ராசி மற்றும் நட்சத்திரத்தைத் தேர்ந்தெடுத்து 12 பொருத்தங்களைப் பார்க்கவும்.',
      kattamStepTitle: 'திருமணக் கட்டப் பொருத்தம்', kattamStepHelp: 'முழுமையான ஜாதகக் கணக்கிற்குப் பிறந்த தேதி, நேரம், இடம் தேவை.',
      kattamPrivacy: 'பிறந்த விவரங்கள் கணக்கிட RightConnect சேவையகத்துக்கு அனுப்பப்படும். விருந்தினர் விவரங்கள் சேமிக்கப்படுவதில்லை; உள்நுழைந்திருந்தால் உங்கள் வரலாற்றில் சேமிக்கப்படும்; எப்போது வேண்டுமானாலும் நீக்கலாம்.', kattamGenerate: 'கட்ட அறிக்கையை உருவாக்கு',
      calculating: 'கணக்கிடப்படுகிறது…', unlockShort: '{price}-ல் திற', unlockBar: 'மங்கலான பகுதிகளைப் படிக்க முழு அறிக்கையைத் திறக்கவும் + PDF',
      accountTitle: 'என் கணக்கு', accountError: 'கணக்கு விவரங்களை ஏற்ற முடியவில்லை. பின்னர் முயற்சிக்கவும்.',
      guestSide: 'உள்நுழைந்தால் கடைசி 30 பொருத்தங்கள் இங்கே சேமிக்கப்படும்; கடைசியாக உள்ளிட்ட விவரங்கள் தானாக நிரப்பப்படும்.',
      adminBadge: 'நிர்வாகி — அனைத்து அறிக்கைகளும் இலவசம். WhatsApp வாடிக்கையாளர்களுக்கு PDF உருவாக்கலாம்.',
      creditsLeft: 'மீதமுள்ள அறிக்கைகள்: {n}', creditsUntil: '{date} வரை', noCredits: 'செயலிலுள்ள பேக் இல்லை.',
      packOffer: '{price}-க்கு {n} அறிக்கைகள் · {days} நாள்', packHelp: 'திருமண தகவல் மையங்கள், தரகர்கள், பல ஜாதகங்கள் பார்ப்பவர்களுக்கு.',
      buyPack: 'பேக் வாங்கு', loginForPack: 'உள்நுழைந்து பேக் வாங்கு', orPack: 'அதிக ஜாதகங்கள் பார்க்கிறீர்களா?',
      packBought: 'பேக் செயல்படுத்தப்பட்டது: {n} அறிக்கைகள்.', noCreditsError: 'பேக்கில் அறிக்கைகள் இல்லை.',
      useCredit: 'பேகில் 1 அறிக்கை பயன்படுத்தித் திற ({n} மீதம்)', useCreditShort: 'பேகில் திற',
      historyTitle: 'முந்தைய பொருத்தங்கள்', historyEmpty: 'இன்னும் பொருத்தம் பார்க்கவில்லை.',
      historyWarning: 'கடைசி {n} முடிவுகள் மட்டும் சேமிக்கப்படும். புதியது சேரும்போது பழையது தானாக நீக்கப்படும் (திறந்த அறிக்கைகளும்). தேவையானதை PDF ஆகச் சேமிக்கவும்.',
      deleteHistory: 'நீக்கு', deleteHistoryConfirm: 'இந்த முடிவை வரலாற்றிலிருந்து நீக்கவா?', lockedEntry: 'பூட்டப்பட்டது',
      level_high: 'உத்தமம்', level_medium: 'மத்திமம்', level_low: 'அதமம்',
      period_high: 'நல்ல காலம்', period_medium: 'கலவை', period_low: 'சவால்', historyJathagam: 'ஜாதகம்',
      chooseJathagamTitle: 'ஜாதகம் (ஒருவருக்கு)',
      chooseJathagamHelp: 'ஒருவரின் பிறந்த விவரம் — ராசி, நவாம்சக் கட்டம், தசை புத்தி, எதிர்காலப் பலன். முன்னோட்டம் இலவசம்; முழு அறிக்கை PDF {price}.',
      jathagamStepTitle: 'ஜாதகம் — பிறந்த விவரங்கள்', jathagamPerson: 'ஜாதகரின் பிறந்த விவரங்கள்', jathagamGenerate: 'ஜாதகம் கணி',
      lockedTitleJathagam: 'முழு ஜாதக அறிக்கை',
      lockedItemsJathagam: ['செவ்வாய், நாக தோஷம் — ஏன், எந்த வீட்டில்', 'ஒன்பது கிரகங்களின் ராசி, பாகை, நட்சத்திரம், நவாம்சம்', 'இப்போதைய, அடுத்த தசை — எந்தத் தேதி வரை, என்ன பலன்', 'அடுத்த 25 ஆண்டுகளின் தசை பலன்', 'வேலை, உடல்நலம், குழந்தை, இல்லறம் — எப்போது முன்னேற்றம்', 'நடப்பு தசையின் ஒன்பது புத்திகள், இறுதிச் சுருக்கம்', 'உங்கள் சாதனத்தில் PDF ஆகப் பதிவிறக்கம்'],
      printReport: 'PDF / அச்சிடு', editBirth: 'பிறப்பு விவரங்களை மாற்று', kattamTimeError: 'இந்த நேர மண்டலத்தில் அந்தப் பிறந்த நேரம் இல்லை அல்லது இருமுறை வருகிறது (பகல் ஒளி சேமிப்பு மாற்றம்). நேரத்தைச் சரிபார்க்கவும்.',
      brideName: 'பெண் பெயர் (விருப்பம்)', groomName: 'பையன் பெயர் (விருப்பம்)',
      brideRasi: 'பெண் ராசி', groomRasi: 'பையன் ராசி',
      brideStar: 'பெண் நட்சத்திரம்', groomStar: 'பையன் நட்சத்திரம்',
      selectRasi: '-- ராசியைத் தேர்ந்தெடுக்கவும் --', selectStar: '-- நட்சத்திரத்தைத் தேர்ந்தெடுக்கவும் --',
      checkRasiMatch: 'அறிக்கையை உருவாக்கு',
      viewKattam: 'கட்டப் பொருத்தத்தைப் பார்க்கவும்', editRasi: 'ராசி விவரங்களை மாற்று',
      selectRasiFirst: '-- முதலில் ராசியைத் தேர்ந்தெடுக்கவும் --', padaSuffix: 'பாதம்',
      brideHeading: 'மணமகள்', groomHeading: 'மணமகன்',
      skip: 'உள்ளடக்கத்திற்குச் செல்ல', language: 'மொழி', views: 'பகுதிகள்', services: 'சேவைகள்',
      chooseService: 'சேவையைத் தேர்ந்தெடுக்கவும்', astrologyServices: 'ஜோதிடம் மற்றும் தொடர்புடைய சேவைகள்', loadingServices: 'சேவைகள் ஏற்றப்படுகின்றன…',
      examKicker: 'போட்டித் தேர்வு உதவி', examTitle: 'போட்டித் தேர்வு விண்ணப்பச் சேவைகள்',
      examDescription: 'தேர்வுக்கு ஏற்ப புகைப்படம், கையொப்பம் மற்றும் ஆவண விதிகளைத் தயாரிக்க உதவும் கருவிகள்.',
      examComing: 'விரைவில்', examServices: 'போட்டித் தேர்வு சேவைகள்',
      examPhoto: 'புகைப்படம்: அளவு, KB, பெயர் / தேதி', examSignature: 'கையொப்பம்: அளவு மற்றும் வடிவம்',
      examDocuments: 'ஆவணங்கள்: PDF அளவு / மாற்றம்',
      catalogueUnavailable: 'அறிக்கை சேவையகத்தை அடைய முடியவில்லை. சேவையகத்தைத் தொடங்கி மீண்டும் முயற்சிக்கவும்.',
      compatibilityOnly: 'திருமணப் பொருத்தம் தனிப் பக்கத்தில் முதலில் உருவாக்கப்படுகிறது. மற்ற சேவைகள் தனித்தனியாக பின்னர் சேர்க்கப்படும்.',
      comingSoon: 'இந்தச் சேவை விரைவில் சேர்க்கப்படும்.',
      nadi: 'நாடி பொருத்தம்', varna: 'வர்ணப் பொருத்தம் (பாரம்பரிய வகைப்பாடு)',
      featureDisabled: 'திருமணப் பொருத்த அறிக்கை இன்னும் இயக்கப்படவில்லை.',
      providerMissing: 'AI வழங்குநரின் URL, மாடல் மற்றும் API key அமைக்கப்படவில்லை.',
      rateSaltMissing: 'AI_REPORT_RATE_SALT பாதுகாப்பாக அமைக்கப்படவில்லை.',
      ephemerisMissing: 'Swiss Ephemeris கணக்கீட்டுத் தொகுப்பு நிறுவப்படவில்லை.',
      login: 'Google மூலம் உள்நுழை', logout: 'வெளியேறு', guest: 'விருந்தினர்', signedIn: 'உள்நுழைந்துள்ளீர்கள்',
      optionalLogin: 'உள்நுழைவு விருப்பமானது. விருந்தினராகவும் அறிக்கை பெறலாம்.',
      tradition: 'பாரம்பரிய நம்பிக்கைகளை அடிப்படையாகக் கொண்டவை; அறிவியல் ஆதாரம் இல்லை. மருத்துவம், நிதி அல்லது முக்கிய முடிவுகளுக்கான ஆலோசனை அல்ல.',
      history: 'முந்தைய அறிக்கைகள்', family: 'குடும்ப விவரங்கள்',
      familyHelp: 'உங்கள் அனுமதியுடன் மட்டும் பிறந்த விவரங்கள் கணக்கில் சேமிக்கப்படும். அறிக்கை பெற சேமிக்க வேண்டியதில்லை.',
      unavailable: 'இப்போது கிடைக்கவில்லை', aiUnavailable: 'AI அறிக்கை சேவை இப்போது கிடைக்கவில்லை. பின்னர் மீண்டும் முயற்சிக்கவும்.',
      networkError: 'இணைப்பில் சிக்கல். இணைய இணைப்பைச் சரிபார்த்து மீண்டும் முயற்சிக்கவும்.',
      requestError: 'கோரிக்கையை நிறைவேற்ற முடியவில்லை. மீண்டும் முயற்சிக்கவும்.',
      invalidError: 'விவரங்களைச் சரிபார்க்கவும். தேதி, நேரம், ஆயத்தொலைவுகள் மற்றும் நேர மண்டலம் சரியாக இருக்க வேண்டும்.',
      authError: 'இந்தச் செயலுக்கு மீண்டும் உள்நுழையவும்.', accessError: 'இந்த அறிக்கையை அணுக முடியவில்லை. உரிமையாளர் கணக்கில் உள்நுழையவும்.',
      onboardingError: 'குடும்ப விவரங்களையும் அறிக்கை வரலாற்றையும் சேமிக்க RightConnect கணக்குப் பதிவை முடிக்கவும். விருந்தினராகத் தொடர வெளியேறலாம்.',
      completeAccount: 'கணக்குப் பதிவை முடி',
      missingError: 'பதிவு கிடைக்கவில்லை.', rateError: 'அதிக கோரிக்கைகள் வந்துள்ளன. சிறிது நேரம் கழித்து முயற்சிக்கவும்.',
      unavailableError: 'சேவை தற்காலிகமாகக் கிடைக்கவில்லை. பின்னர் முயற்சிக்கவும்.',
      reload: 'மீண்டும் ஏற்று', back: 'சேவைகளுக்குத் திரும்பு', birth: 'பிறந்த விவரங்கள்', bride: 'மணமகள் பிறந்த விவரங்கள்', groom: 'மணமகன் பிறந்த விவரங்கள்',
      name: 'பெயர் (விருப்பம்)', brideDefaultName: 'பெயர் இல்லையெனில்: பெண்', groomDefaultName: 'பெயர் இல்லையெனில்: பையன்',
      birthDate: 'பிறந்த தேதி', birthTime: 'பிறந்த நேரம்', localTime: 'பிறந்த இடத்தின் உள்ளூர் நேரம்; நேரம் தெரியாவிட்டால் ஊகிக்க வேண்டாம்.',
      cityPreset: 'நகரத் தேர்வு', manualCity: 'வேறு இடம் / கைமுறை', place: 'பிறந்த இடம்', latitude: 'அட்சரேகை', longitude: 'தீர்க்கரேகை', timezone: 'IANA நேர மண்டலம்',
      birthCityOptional: 'பிறந்த ஊர் (விருப்பம்)',
      kattamPlaceHelp: 'ஊர்ப் பெயரைத் தட்டச்சு செய்யவும். காலியாக விட்டால் அல்லது ஊர் அடையாளம் காணப்படாவிட்டால் சென்னை அடிப்படையில் கணக்கிடப்படும்.',
      placeUnknown: '{name}: “{place}” ஊர் அடையாளம் காணப்படவில்லை; சென்னை (இந்திய நேரம்) அடிப்படையில் கணக்கிடப்பட்டது. லக்னம் சிறிது மாறலாம்.',
      placeMissing: '{name}: பிறந்த ஊர் கொடுக்கப்படவில்லை; சென்னை அடிப்படையில் கணக்கிடப்பட்டது. லக்னம் சிறிது மாறலாம்.',
      chooseTitle: 'என்ன பார்க்க வேண்டும்?', chooseRasiTitle: 'ராசி பொருத்தம்', chooseKattamTitle: 'கட்டப் பொருத்தம்',
      chooseRasiHelp: 'ராசி, நட்சத்திரம் மட்டும் தெரிந்தால் — 12 பொருத்தங்கள். பிறகு கட்டப் பொருத்தமும் பார்க்கலாம்.',
      chooseKattamHelp: 'பிறந்த தேதி, நேரம் தெரிந்தால் — நேரடியாக முழு ஜாதகப் பொருத்தம்: தோஷம், தசை, எதிர்காலம். முன்னோட்டம் இலவசம்; முழு அறிக்கை PDF {price}.',
      freePreview: 'இலவச முன்னோட்டம்', lockedTitle: 'முழு கட்டப் பொருத்த அறிக்கை',
      lockedLead: 'மேலே உள்ளது இலவச முன்னோட்டம் மட்டும். முழு அறிக்கையில்:',
      lockedItems: ['இருவருக்கும் பொருந்துமா — தோஷ சாம்யத்தின் முழு விளக்கம்', 'இப்போதைய, அடுத்த தசை — எந்தத் தேதி வரை, என்ன பலன்', 'அடுத்த 25 ஆண்டுகள் — இருவரின் தசையும் சேர்த்து', 'வேலை, உடல்நலம், குழந்தை, இல்லறம் — எப்போது முன்னேற்றம்', 'கட்டப் பொருத்த ஆய்வு — பாப சாம்யம், தசா சந்தி', 'இறுதிச் சுருக்கம், ராசி – நவாம்சக் கட்டங்கள், கிரக நிலைகள்', 'உங்கள் சாதனத்தில் PDF ஆகப் பதிவிறக்கம்'],
      payUnlock: '{price} செலுத்தி முழு அறிக்கை PDF பெறுக',
      payNote: 'Razorpay மூலம் பாதுகாப்பான கட்டணம் — UPI, கார்டு, நெட்பேங்கிங். பிறந்த விவரங்கள் கட்டணச் சேவைக்கு அனுப்பப்படுவதில்லை. ஒரு கட்டணம் இந்த இருவரின் அறிக்கைக்கு மட்டும்.',
      payOpening: 'பாதுகாப்பான கட்டணப் பக்கம் திறக்கிறது…', payVerifying: 'கட்டணம் சரிபார்க்கப்படுகிறது…',
      payPending: 'கட்டணம் பெறப்பட்டது; உறுதிப்படுத்தல் நிலுவையில் உள்ளது. மீண்டும் கட்டணம் செலுத்த வேண்டாம். சிறிது நேரம் கழித்து “நிலையைச் சரிபார்” அழுத்தவும்.',
      payFailed: 'கட்டணம் நிறைவேறவில்லை. பணம் கழிக்கப்பட்டிருந்தால் தானாகத் திருப்பி அளிக்கப்படும். மீண்டும் முயற்சிக்கலாம்.',
      payCancelled: 'கட்டணம் ரத்து செய்யப்பட்டது. முன்னோட்டம் தொடர்ந்து கிடைக்கும்.',
      payUnavailable: 'கட்டண வசதி இப்போது கிடைக்கவில்லை. பின்னர் முயற்சிக்கவும்.',
      payVerifyError: 'கட்டணத்தைச் சரிபார்க்க முடியவில்லை. மீண்டும் கட்டணம் செலுத்த வேண்டாம்; “நிலையைச் சரிபார்” அழுத்தவும்.',
      paidThanks: 'நன்றி! கட்டணம் உறுதியானது. PDF பதிவிறக்கம் தொடங்கவில்லை எனில் “PDF பதிவிறக்கு” அழுத்தவும்.',
      downloadPdf: 'PDF பதிவிறக்கு', pdfPreparing: 'PDF தயாராகிறது…', pdfReady: 'PDF உங்கள் சாதனத்தில் பதிவிறக்கப்பட்டது.',
      pdfError: 'PDF உருவாக்க முடியவில்லை. “PDF / அச்சிடு” மூலம் சேமிக்கலாம்.', pdfGenerated: 'உருவாக்கிய நாள்',
      backToChoice: 'பொருத்த வகைக்குத் திரும்பு',
      locationHelp: 'நகர மைய ஆயத்தொலைவுகள் மட்டுமே. பிறந்த இடத்திற்கேற்ப திருத்தவும். மற்ற இடங்களுக்கு சரியான ஆயத்தொலைவுகளை நீங்களே உள்ளிடவும்; தானியங்கி இடத்தேடல் இல்லை.',
      compatibilityPlaceHelp: 'பிறந்த ஊரைத் தேர்ந்தெடுக்கவும்; நேர மண்டலம் தானாக நிரப்பப்படும். இந்தப் பொருத்தக் கணக்கிற்கு அட்சரேகை, தீர்க்கரேகை தேவையில்லை.',
      confirmLocation: 'பிறந்த இடம், அட்சரேகை, தீர்க்கரேகை மற்றும் நேர மண்டலத்தைச் சரிபார்த்து உறுதிப்படுத்துகிறேன்.',
      timezoneHelp: 'எ.கா. Asia/Kolkata. பிறந்த தேதிக்கான உள்ளூர் நேர மண்டலத்தை உறுதிப்படுத்தவும்.',
      savedMember: 'சேமித்த குடும்ப உறுப்பினர்', manualMember: 'புதிய விவரங்களை உள்ளிடு',
      fullName: 'முழுப் பெயர் (ஆங்கில எழுத்துகளில்)', englishNameHelp: 'எண் கணிதத்திற்கு வழக்கமாகப் பயன்படுத்தும் ஆங்கிலப் பெயர் எழுத்துக்கூட்டலை உள்ளிடவும்.',
      englishNameError: 'பெயரை ஆங்கில எழுத்துகளில் உள்ளிடவும்.', invalidTimezone: 'சரியான IANA நேர மண்டலத்தை உள்ளிடவும்.',
      facing: 'வீடு எதிர்நோக்கும் திசை', main_door: 'முதன்மை வாசல் திசை', kitchen: 'சமையலறை அமைந்த திசை', bedroom: 'படுக்கையறை அமைந்த திசை',
      directionHelp: 'வீட்டின் மையத்திலிருந்து அறைகள் அமைந்த திசையைத் தேர்ந்தெடுக்கவும்.',
      N: 'வடக்கு', NE: 'வடகிழக்கு', E: 'கிழக்கு', SE: 'தென்கிழக்கு', S: 'தெற்கு', SW: 'தென்மேற்கு', W: 'மேற்கு', NW: 'வடமேற்கு',
      gender: 'பெயர் வகை', neutral: 'பாலினச் சார்பற்றது', male: 'ஆண்', female: 'பெண்', rasi: 'ராசி', period: 'காலம்', daily: 'தினசரி', weekly: 'வாராந்திர',
      reportConsent: 'பிறந்த விவரங்கள் சரியானவை என உறுதிப்படுத்தி, அறிக்கைக்காக அவற்றைத் தற்காலிகமாகச் சேமித்து AI சேவை வழங்குநருக்கு அனுப்ப அனுமதிக்கிறேன். குடும்பப் பட்டியலில் தானாகச் சேமிக்கப்படாது.',
      generate: 'அறிக்கை உருவாக்கு', generating: 'அறிக்கை தயாராகிறது…', loading: 'ஏற்றப்படுகிறது…', completed: 'தயார்', pending: 'தயாராகிறது', failed: 'உருவாக்க முடியவில்லை',
      failedHelp: 'இந்த அறிக்கை முழுமையடையவில்லை. இதே பதிவை மீண்டும் முயற்சிக்கலாம்.', pendingHelp: 'அறிக்கை இன்னும் தயாராகிறது. சிறிது நேரம் கழித்து நிலையைச் சரிபார்க்கவும்.',
      retry: 'மீண்டும் முயற்சி', refresh: 'நிலையைச் சரிபார்', open: 'திற', edit: 'விவரங்களைத் திருத்து', editUnavailable: 'அசல் விவரங்கள் இந்தப் பக்க நினைவில் இல்லை. புதிய அறிக்கைக்கான விவரங்களை உள்ளிடவும்.',
      copy: 'நகலெடு', download: '.txt பதிவிறக்கு', share: 'பகிர்', copied: 'அறிக்கை நகலெடுக்கப்பட்டது.', copyError: 'நகலெடுக்க முடியவில்லை. .txt கோப்பைப் பதிவிறக்கலாம்.',
      shareError: 'பகிர முடியவில்லை. .txt கோப்பைப் பதிவிறக்கலாம்.', reportTitle: 'அறிக்கை', reportId: 'அறிக்கை எண்',
      noHistory: 'முந்தைய அறிக்கைகள் இல்லை.', recovery: 'இந்த அமர்வின் அறிக்கைகள்', recoveryHelp: 'இந்த உலாவித் தாவலில் மட்டும் மீண்டும் திறக்கலாம். விருந்தினர் அணுகல் விசை பிறந்த விவரங்கள் இல்லாமல் தற்காலிகமாக வைக்கப்படும். தாவலை மூடினால் அணுகல் இழக்கப்படலாம்.',
      storageError: 'இந்தத் தாவலில் மீட்பு அணுகல் விசையைச் சேமிக்க முடியவில்லை. அறிக்கையைப் பதிவிறக்கவும்; பக்கத்தைப் புதுப்பித்தால் விருந்தினர் அணுகல் இழக்கப்படும்.',
      emptyFamily: 'சேமித்த குடும்ப உறுப்பினர்கள் இல்லை.', addMember: 'உறுப்பினரைச் சேர்', memberLabel: 'உறுப்பினர் அடையாளப் பெயர்',
      saveConsent: 'இந்தப் பிறந்த விவரங்களை என் கணக்கில் சேமிக்க வெளிப்படையாக அனுமதிக்கிறேன்.',
      saveMember: 'அனுமதியுடன் சேமி', updateMember: 'அனுமதியுடன் மாற்றங்களைச் சேமி', saved: 'குடும்ப விவரங்கள் சேமிக்கப்பட்டன.',
      editMember: 'திருத்து', deleteMember: 'நீக்கு', deleteConfirm: 'இந்த உறுப்பினரின் சேமித்த பிறந்த விவரங்களை நீக்கவா?', deleted: 'உறுப்பினர் நீக்கப்பட்டார்.',
      cancel: 'ரத்து', loginUnavailable: 'Google உள்நுழைவு இப்போது கிடைக்கவில்லை. விருந்தினராகத் தொடரலாம்.', loginFailed: 'உள்நுழைவு நிறைவேறவில்லை. மீண்டும் முயற்சிக்கவும்.',
      familyError: 'குடும்ப விவரங்களை ஏற்ற முடியவில்லை. மீண்டும் முயற்சிக்கவும்.', operationBusy: 'நடைபெறும் கோரிக்கை முடியும் வரை காத்திருக்கவும்.',
      dateError: '1900 முதல் இன்று வரையிலான பிறந்த தேதியை உள்ளிடவும்.', invalidResponse: 'சேவையிலிருந்து சரியான பதில் வரவில்லை. மீண்டும் முயற்சிக்கவும்.',
      requiredField: 'இந்த விவரத்தை நிரப்பவும்.', requiredConsent: 'தொடர இந்த உறுதிப்படுத்தல் தேவை.',
      invalidField: 'இந்த விவரத்தைச் சரிபார்த்து சரியாக உள்ளிடவும்.', invalidNumber: 'குறிப்பிட்ட வரம்பிற்குள் சரியான எண்ணை உள்ளிடவும்.'
    },
    en: {
      appTitle: 'Tamil Astrology & Arts AI Reports', eyebrow: 'Traditional arts',
      servicesHubTitle: 'Services', servicesHubEyebrow: 'RightConnect services', skip: 'Skip to content', language: 'Language', views: 'Views', services: 'Services',
      astrologyHubTitle: 'Astrology & related services', astrologyHubEyebrow: 'Traditional arts', allServiceCategories: 'All service categories',
      compatibilityPageTitle: 'Marriage Compatibility & Horoscope', compatibilityNav: 'Matching & horoscope',
      compatibilityDisclaimer: 'This compares twelve traditional rules. They are not scientific predictions or a marriage-success percentage. Varna is a historical caste-coded classification; it does not determine anyone’s worth.',
      backToRasi: 'Back to Rasi results',
      rasiStepTitle: 'Rasi matching', rasiStepHelp: 'Choose both Rasis and Nakshatras to see the twelve traditional checks.',
      kattamStepTitle: 'Detailed Jathaka Kattam matching', kattamStepHelp: 'A fuller chart calculation needs each person’s birth date, time and place.',
      kattamPrivacy: 'Birth details are sent to the RightConnect server to calculate the report. Guest details are not stored; when signed in they are saved to your history, which you can delete any time.', kattamGenerate: 'Create Kattam report',
      calculating: 'Calculating…', unlockShort: 'Unlock for {price}', unlockBar: 'Unlock the blurred parts and get the PDF',
      accountTitle: 'My account', accountError: 'Could not load your account. Please try again later.',
      guestSide: 'Sign in to keep your last 30 matches here and have your last entered details filled in automatically.',
      adminBadge: 'Admin — all reports are free. Create PDFs for WhatsApp customers.',
      creditsLeft: 'Reports left: {n}', creditsUntil: 'until {date}', noCredits: 'No active pack.',
      packOffer: '{n} reports for {price} · {days} days', packHelp: 'For matrimony centres, brokers and anyone checking many horoscopes.',
      buyPack: 'Buy pack', loginForPack: 'Sign in to buy a pack', orPack: 'Checking many horoscopes?',
      packBought: 'Pack activated: {n} reports.', noCreditsError: 'No reports left in your pack.',
      useCredit: 'Open with 1 pack report ({n} left)', useCreditShort: 'Open with pack',
      historyTitle: 'Previous matches', historyEmpty: 'No matches yet.',
      historyWarning: 'Only the last {n} results are kept. A new one removes the oldest automatically (unlocked reports too). Save the ones you need as PDF.',
      deleteHistory: 'Delete', deleteHistoryConfirm: 'Remove this result from your history?', lockedEntry: 'Locked',
      level_high: 'Good', level_medium: 'Average', level_low: 'Weak',
      period_high: 'Good period', period_medium: 'Mixed', period_low: 'Challenging', historyJathagam: 'Horoscope',
      chooseJathagamTitle: 'Horoscope (one person)',
      chooseJathagamHelp: 'One person’s birth details — Rasi and Navamsa charts, dasa–bhukti and future reading. Free preview; full report PDF {price}.',
      jathagamStepTitle: 'Horoscope — birth details', jathagamPerson: 'Birth details', jathagamGenerate: 'Create horoscope',
      lockedTitleJathagam: 'Full horoscope report',
      lockedItemsJathagam: ['Chevvai and Naga dosha — why, and from which house', 'All nine planets — sign, degree, Nakshatra and Navamsa', 'Current and next dasa — until which date and what it brings', 'Dasa results for the next 25 years', 'Career, health, children, married life — when progress comes', 'The nine bhuktis of the current dasa and a final summary', 'Downloaded to your device as a PDF'],
      printReport: 'PDF / Print', editBirth: 'Change birth details', kattamTimeError: 'This birth time does not exist or occurs twice in that timezone (daylight-saving change). Please check the time.',
      brideName: 'Bride name (optional)', groomName: 'Groom name (optional)',
      brideRasi: 'Bride Rasi', groomRasi: 'Groom Rasi',
      brideStar: 'Bride Nakshatra', groomStar: 'Groom Nakshatra',
      selectRasi: '-- Select Rasi --', selectStar: '-- Select Nakshatra --',
      checkRasiMatch: 'Create report',
      viewKattam: 'Check detailed Kattam matching', editRasi: 'Change Rasi details',
      selectRasiFirst: '-- Select a Rasi first --', padaSuffix: 'pada',
      brideHeading: 'Bride', groomHeading: 'Groom',
      chooseService: 'Choose a service', astrologyServices: 'Astrology & related services', loadingServices: 'Loading services…', login: 'Sign in with Google', logout: 'Sign out', guest: 'Guest', signedIn: 'Signed in',
      examKicker: 'Competitive exam help', examTitle: 'Competitive exam application services',
      examDescription: 'Tools to prepare photos, signatures and documents to match each exam’s requirements.',
      examComing: 'Coming soon', examServices: 'Competitive exam services',
      examPhoto: 'Photo: dimensions, file size, name / date', examSignature: 'Signature: dimensions and format',
      examDocuments: 'Documents: PDF size / conversion',
      catalogueUnavailable: 'The report API could not be reached. Start the server and try again.',
      compatibilityOnly: 'Marriage compatibility is being built first on its own page. The other services will follow as separate pages.',
      comingSoon: 'This service will be added later.', nadi: 'Nadi Porutham', varna: 'Varna Porutham (traditional classification)',
      featureDisabled: 'Marriage report generation has not been enabled.',
      providerMissing: 'Configure the AI provider URL, model and API key.',
      rateSaltMissing: 'Configure AI_REPORT_RATE_SALT as a server-side secret.',
      ephemerisMissing: 'Install the Swiss Ephemeris calculation package.',
      optionalLogin: 'Sign-in is optional. Guests can generate reports.',
      tradition: 'Based on traditional beliefs, without scientific evidence. Not advice for medical, financial or other important decisions.',
      history: 'Report history', family: 'Family details', familyHelp: 'Birth details are saved to your account only with your permission. Saving is not required for reports.',
      unavailable: 'Currently unavailable', aiUnavailable: 'AI reports are currently unavailable. Please try again later.',
      networkError: 'Connection problem. Check your internet connection and try again.', requestError: 'Could not complete the request. Please try again.',
      invalidError: 'Check your details, including date, time, coordinates and timezone.', authError: 'Please sign in again for this action.',
      accessError: 'This report cannot be accessed. Sign in with its owner account.', missingError: 'Record not found.', rateError: 'Too many requests. Please try again shortly.',
      onboardingError: 'Complete RightConnect registration to save family details and account history. You can sign out to continue as a guest.',
      completeAccount: 'Complete registration',
      unavailableError: 'The service is temporarily unavailable. Please try again later.', reload: 'Reload', back: 'Back to services',
      birth: 'Birth details', bride: 'Bride’s details (பெண்)', groom: 'Groom’s details (பையன்)', name: 'Name (optional)',
      brideDefaultName: 'If blank, the report will say பெண்', groomDefaultName: 'If blank, the report will say பையன்',
      birthDate: 'Birth date', birthTime: 'Birth time',
      localTime: 'Local time at the birthplace. Do not guess an unknown birth time.', cityPreset: 'City preset', manualCity: 'Other place / manual',
      place: 'Birthplace', latitude: 'Latitude', longitude: 'Longitude', timezone: 'IANA timezone',
      birthCityOptional: 'Birth city (optional)',
      kattamPlaceHelp: 'Type the birth city. If it is left blank or not recognised, Chennai is used for the calculation.',
      placeUnknown: '{name}: “{place}” was not recognised, so Chennai (Indian time) was used. The Lagna may shift slightly.',
      placeMissing: '{name}: no birth city was given, so Chennai was used. The Lagna may shift slightly.',
      chooseTitle: 'What would you like to check?', chooseRasiTitle: 'Rasi matching', chooseKattamTitle: 'Kattam matching',
      chooseRasiHelp: 'If you only know the Rasi and Nakshatra — the 12 checks. You can continue to Kattam matching afterwards.',
      chooseKattamHelp: 'If you know the birth date and time — go straight to full chart matching: dosha, dasa and future. Free preview; full report PDF {price}.',
      freePreview: 'Free preview', lockedTitle: 'Full Kattam porutham report',
      lockedLead: 'Above is only the free preview. The full report includes:',
      lockedItems: ['Do the two charts match — the full dosha-balance explanation', 'Current and next dasa — until which date and what it brings', 'The next 25 years — both dasas side by side', 'Career, health, children, married life — when progress comes', 'Kattam compatibility checks — papa samyam and dasa sandhi', 'Final summary, Rasi and Navamsa charts, planet positions', 'Downloaded to your device as a PDF'],
      payUnlock: 'Pay {price} & get the full report PDF',
      payNote: 'Secure payment via Razorpay — UPI, cards, netbanking. Birth details are never sent to the payment service. One payment covers this couple’s report.',
      payOpening: 'Opening secure payment…', payVerifying: 'Verifying payment…',
      payPending: 'Payment received; confirmation is pending. Do not pay again. Press “Check status” shortly.',
      payFailed: 'The payment did not go through. Any amount debited is refunded automatically. You can try again.',
      payCancelled: 'Payment cancelled. The preview remains available.',
      payUnavailable: 'Payments are currently unavailable. Please try again later.',
      payVerifyError: 'The payment could not be verified. Do not pay again; press “Check status”.',
      paidThanks: 'Thank you! Payment confirmed. If the PDF did not start downloading, press “Download PDF”.',
      downloadPdf: 'Download PDF', pdfPreparing: 'Preparing PDF…', pdfReady: 'The PDF has been downloaded to your device.',
      pdfError: 'Could not create the PDF. You can save it with “PDF / Print”.', pdfGenerated: 'Generated on',
      backToChoice: 'Back to matching type',
      locationHelp: 'Presets are city-centre coordinates. Adjust to the actual birthplace. Enter accurate coordinates for other places; there is no automatic geocoding.',
      compatibilityPlaceHelp: 'Choose the birthplace to fill its timezone. Latitude and longitude are not needed for this compatibility calculation.',
      confirmLocation: 'I have checked and confirm the birthplace, latitude, longitude and timezone.', timezoneHelp: 'For example, Asia/Kolkata. Confirm the local timezone for the birth date.',
      savedMember: 'Saved family member', manualMember: 'Enter new details', fullName: 'Full name (English spelling)', englishNameHelp: 'Use the English spelling of the name normally used for numerology.',
      englishNameError: 'Enter the name in English letters.', invalidTimezone: 'Enter a valid IANA timezone.',
      facing: 'House facing direction', main_door: 'Main door direction', kitchen: 'Kitchen location', bedroom: 'Bedroom location', directionHelp: 'Choose room directions relative to the centre of the house.',
      N: 'North', NE: 'Northeast', E: 'East', SE: 'Southeast', S: 'South', SW: 'Southwest', W: 'West', NW: 'Northwest',
      gender: 'Name category', neutral: 'Gender neutral', male: 'Male', female: 'Female', rasi: 'Rasi', period: 'Period', daily: 'Daily', weekly: 'Weekly',
      reportConsent: 'I confirm these birth details are accurate and consent to temporary report storage and sending them to the AI provider. They will not be automatically saved to my family list.',
      generate: 'Generate report', generating: 'Preparing your report…', loading: 'Loading…', completed: 'Ready', pending: 'Preparing', failed: 'Generation failed',
      failedHelp: 'This report did not complete. You can retry the same record.', pendingHelp: 'The report is still being prepared. Check its status again shortly.',
      retry: 'Retry', refresh: 'Check status', open: 'Open', edit: 'Edit details', editUnavailable: 'Original details are not in this page’s memory. Enter details for a new report.',
      copy: 'Copy', download: 'Download .txt', share: 'Share', copied: 'Report copied.', copyError: 'Could not copy. You can download the .txt file.', shareError: 'Could not share. You can download the .txt file.',
      reportTitle: 'Report', reportId: 'Report ID', noHistory: 'No previous reports.', recovery: 'Reports in this session',
      recoveryHelp: 'Reopen reports in this browser tab. A temporary guest access key is kept without birth details. Closing the tab may lose access.',
      storageError: 'The recovery key could not be saved in this tab. Download your report; refreshing may lose guest access.',
      emptyFamily: 'No saved family members.', addMember: 'Add member', memberLabel: 'Member label', saveConsent: 'I explicitly consent to saving these birth details to my account.',
      saveMember: 'Save with consent', updateMember: 'Save changes with consent', saved: 'Family details saved.', editMember: 'Edit', deleteMember: 'Delete',
      deleteConfirm: 'Delete this member’s saved birth details?', deleted: 'Member deleted.', cancel: 'Cancel',
      loginUnavailable: 'Google sign-in is currently unavailable. You can continue as a guest.', loginFailed: 'Sign-in did not complete. Please try again.',
      familyError: 'Could not load family details. Please try again.', operationBusy: 'Please wait for the current request to finish.',
      dateError: 'Enter a birth date between 1900 and today.', invalidResponse: 'The service returned an invalid response. Please try again.',
      requiredField: 'Please fill in this detail.', requiredConsent: 'This confirmation is required to continue.',
      invalidField: 'Please check and enter a valid value.', invalidNumber: 'Enter a valid number within the specified range.'
    }
  };
  const descriptors = [
    { key: 'horoscope', page: 'thirumana-porutham.html?service=jathagam', icon: 'orbit', ta: ['ஜாதகம்', 'பிறந்த நேரம் மற்றும் இடத்தின் அடிப்படையில் பாரம்பரிய ஜாதக விளக்கம்.'], en: ['Horoscope', 'A traditional interpretation based on birth time and place.'] },
    { key: 'compatibility', page: 'thirumana-porutham.html', icon: 'heart-handshake', ta: ['திருமணப் பொருத்தம்', 'பன்னிரண்டு பாரம்பரியப் பொருத்தங்களை ஒப்பிடும் தனிப்பட்ட அறிக்கை.'], en: ['Compatibility', 'A dedicated report comparing twelve traditional checks.'] },
    { key: 'numerology', page: 'numerology.html', icon: 'binary', ta: ['எண் கணிதம்', 'ஆங்கிலப் பெயர் மற்றும் பிறந்த தேதியின் எண் கணித விளக்கம்.'], en: ['Numerology', 'Traditional number interpretations of an English name and birth date.'] },
    { key: 'vastu', page: 'vastu.html', icon: 'house', ta: ['வாஸ்து', 'வீடு மற்றும் அறைகளின் திசைகள் பற்றிய பாரம்பரியக் கருத்துகள்.'], en: ['Vastu', 'Traditional perspectives on home and room directions.'] },
    { key: 'gemstone', page: 'gemstone.html', icon: 'gem', ta: ['ரத்தினக் கற்கள்', 'பிறந்த விவரங்களின் அடிப்படையில் பாரம்பரிய ரத்தின விளக்கம்.'], en: ['Gemstones', 'Traditional gemstone interpretations using birth details.'] },
    { key: 'baby-names', page: 'baby-names.html', icon: 'baby', ta: ['குழந்தைப் பெயர்கள்', 'பிறந்த விவரங்களுடன் குழந்தைப் பெயர் பரிந்துரைகள்.'], en: ['Baby names', 'Name suggestions using birth details and a name category.'] },
    { key: 'forecast', page: 'rasi-forecast.html', icon: 'sun', ta: ['ராசி பலன்', 'தேர்ந்தெடுத்த ராசிக்கான தினசரி அல்லது வாராந்திர பாரம்பரியப் பலன்.'], en: ['Rasi forecast', 'Daily or weekly traditional readings for your selected rasi.'] }
  ];
  const cities = [
    ['Chennai', 'சென்னை', 13.0827, 80.2707, 'Asia/Kolkata', ['Madras', 'மெட்ராஸ்']],
    ['Madurai', 'மதுரை', 9.9252, 78.1198, 'Asia/Kolkata'],
    ['Coimbatore', 'கோயம்புத்தூர்', 11.0168, 76.9558, 'Asia/Kolkata', ['Kovai', 'கோவை']],
    ['Trichy', 'திருச்சி', 10.7905, 78.7047, 'Asia/Kolkata', ['Tiruchirappalli', 'Tiruchi', 'திருச்சிராப்பள்ளி']],
    ['Salem', 'சேலம்', 11.6643, 78.146, 'Asia/Kolkata'],
    ['Tirunelveli', 'திருநெல்வேலி', 8.7139, 77.7567, 'Asia/Kolkata', ['Nellai', 'நெல்லை']],
    ['Erode', 'ஈரோடு', 11.341, 77.7172, 'Asia/Kolkata'],
    ['Vellore', 'வேலூர்', 12.9165, 79.1325, 'Asia/Kolkata'],
    ['Thanjavur', 'தஞ்சாவூர்', 10.787, 79.1378, 'Asia/Kolkata', ['Tanjore', 'தஞ்சை']],
    ['Thoothukudi', 'தூத்துக்குடி', 8.7642, 78.1348, 'Asia/Kolkata', ['Tuticorin']],
    ['Nagercoil', 'நாகர்கோவில்', 8.1833, 77.4119, 'Asia/Kolkata'],
    ['Puducherry', 'புதுச்சேரி', 11.9416, 79.8083, 'Asia/Kolkata', ['Pondicherry', 'Pondy', 'பாண்டிச்சேரி']],
    ['Bengaluru', 'பெங்களூரு', 12.9716, 77.5946, 'Asia/Kolkata', ['Bangalore', 'பெங்களூர்']],
    ['Jaffna', 'யாழ்ப்பாணம்', 9.6615, 80.0255, 'Asia/Colombo'],
    ['Colombo', 'கொழும்பு', 6.9271, 79.8612, 'Asia/Colombo'],
    ['Singapore', 'சிங்கப்பூர்', 1.3521, 103.8198, 'Asia/Singapore'],
    ['Kuala Lumpur', 'கோலாலம்பூர்', 3.139, 101.6869, 'Asia/Kuala_Lumpur'],
    ['Dubai', 'துபாய்', 25.2048, 55.2708, 'Asia/Dubai'],
    ['London', 'லண்டன்', 51.5074, -0.1278, 'Europe/London']
  ];
  const rasis = {
    ta: ['மேஷம்', 'ரிஷபம்', 'மிதுனம்', 'கடகம்', 'சிம்மம்', 'கன்னி', 'துலாம்', 'விருச்சிகம்', 'தனுசு', 'மகரம்', 'கும்பம்', 'மீனம்'],
    en: ['Mesha (Aries)', 'Rishabha (Taurus)', 'Mithuna (Gemini)', 'Kataka (Cancer)', 'Simha (Leo)', 'Kanya (Virgo)', 'Tula (Libra)', 'Vrischika (Scorpio)', 'Dhanus (Sagittarius)', 'Makara (Capricorn)', 'Kumbha (Aquarius)', 'Meena (Pisces)']
  };
  const nakshatras = {
    ta: ['அசுவினி', 'பரணி', 'கார்த்திகை', 'ரோகிணி', 'மிருகசீரிடம்', 'திருவாதிரை', 'புனர்பூசம்', 'பூசம்', 'ஆயில்யம்', 'மகம்', 'பூரம்', 'உத்திரம்', 'அஸ்தம்', 'சித்திரை', 'சுவாதி', 'விசாகம்', 'அனுஷம்', 'கேட்டை', 'மூலம்', 'பூராடம்', 'உத்திராடம்', 'திருவோணம்', 'அவிட்டம்', 'சதயம்', 'பூரட்டாதி', 'உத்திரட்டாதி', 'ரேவதி'],
    en: ['Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashirsha', 'Ardra', 'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati']
  };
  const state = {
    language: 'ta', services: [], aiAvailable: false, selected: null, session: null,
    client: null, members: [], membersLoaded: false, report: null, inputs: null,
    busy: false, view: 'services', familyEditor: null, capabilities: new Map(),
    compatibilityStep: 'choose', kattamFrom: null, quickMatch: null,
    authVersion: 0, reportVersion: 0, storageWarning: false, catalogueError: null,
    kattamPrice: 9900, kattamProofs: {}, kattamPaying: false, kattamPending: null, kattamPayMessage: '', pdfBusy: false,
    account: null, packOffer: { amount_paise: 29900, reports: 20, days: 90, available: true }, packConfirming: false
  };
  const $ = selector => document.querySelector(selector);
  const t = key => words[state.language][key] || words.ta[key] || key;
  const text = (tag, value, className) => {
    const element = document.createElement(tag);
    if (value !== undefined) element.textContent = value;
    if (className) element.className = className;
    return element;
  };
  const error = key => Object.assign(new Error(key), { key });
  const message = failure => t(failure && failure.key ? failure.key : 'requestError');
  const notice = value => {
    $('#global-status').textContent = value;
    $('#global-status').hidden = !value;
  };
  const titleFor = descriptor => {
    const service = state.services.find(item => item.key === descriptor.key);
    return service && service[`title_${state.language}`] || descriptor[state.language][0];
  };
  const descriptorFor = key => descriptors.find(item => item.key === key);
  function icons() {
    try { if (window.lucide) window.lucide.createIcons(); } catch (_) { return; }
  }
  function button(label, action, style = 'secondary', icon) {
    const control = text('button', undefined, `button ${style}`);
    control.type = 'button';
    if (icon) {
      const symbol = text('i');
      symbol.dataset.lucide = icon;
      symbol.setAttribute('aria-hidden', 'true');
      control.append(symbol);
    }
    control.append(text('span', label));
    control.addEventListener('click', action);
    return control;
  }
  function dateLabel(value) {
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? '' : new Intl.DateTimeFormat(state.language === 'ta' ? 'ta-IN' : 'en-GB', { dateStyle: 'medium', timeStyle: 'short' }).format(parsed);
  }
  function validReport(value) {
    return value && typeof value.id === 'string' && ['completed', 'failed', 'pending'].includes(value.status) && typeof value.service_type === 'string';
  }
  async function request(path, { method = 'GET', body, token, authenticated = false } = {}) {
    if (authenticated && !state.session) throw error('authError');
    const headers = { Accept: 'application/json' };
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (token) headers['X-Report-Token'] = token;
    if (state.session) headers.Authorization = `Bearer ${state.session.access_token}`;
    let response;
    try {
      response = await fetch(`${API}${path}`, { method, headers, body: body === undefined ? undefined : JSON.stringify(body), cache: 'no-store', credentials: 'omit' });
    } catch (_) { throw error('networkError'); }
    if (!response.ok) {
      if (response.status === 403) {
        const problem = await response.json().catch(() => ({}));
        if (problem.detail === 'Complete account onboarding before using AI reports while signed in') throw error('onboardingError');
      }
      const key = { 400: 'invalidError', 401: 'authError', 403: 'accessError', 404: 'missingError', 409: 'operationBusy', 422: 'invalidError', 429: 'rateError', 502: 'unavailableError', 503: 'unavailableError', 504: 'unavailableError' }[response.status];
      throw error(key || 'requestError');
    }
    if (response.status === 204 || method === 'DELETE') return null;
    try { return await response.json(); } catch (_) { throw error('invalidResponse'); }
  }
  function loadCapabilities() {
    try {
      const stored = JSON.parse(sessionStorage.getItem(CAPABILITY_KEY) || '[]');
      if (Array.isArray(stored)) for (const entry of stored) {
        if (entry && typeof entry.id === 'string' && typeof entry.token === 'string' && /^[A-Za-z0-9_-]{43}$/.test(entry.token)) state.capabilities.set(entry.id, entry.token);
      }
    } catch (_) { state.storageWarning = true; }
  }
  function keepCapability(id, token) {
    if (!token) return;
    state.capabilities.set(id, token);
    try {
      sessionStorage.setItem(CAPABILITY_KEY, JSON.stringify(Array.from(state.capabilities, ([reportId, capability]) => ({ id: reportId, token: capability }))));
    } catch (_) { state.storageWarning = true; notice(t('storageError')); }
    renderRecovery();
  }
  function newToken() {
    const bytes = new Uint8Array(32);
    crypto.getRandomValues(bytes);
    return btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }
  function setBusy(value) {
    state.busy = value;
    document.querySelectorAll('[data-lock], [data-view], #language, #login, #logout').forEach(control => {
      control.disabled = value || (control.id === 'login' && !state.client);
    });
    document.querySelectorAll('#input-panel form, .family-editor').forEach(form => form.setAttribute('aria-busy', String(value)));
  }
  async function perform(work, statusElement, statusKey = 'loading') {
    if (state.busy) return;
    setBusy(true);
    notice('');
    let failureMessage = '';
    if (statusElement) {
      statusElement.hidden = false;
      statusElement.textContent = t(statusKey);
      statusElement.dataset.loading = 'true';
      statusElement.dataset.error = 'false';
    }
    try { await work(); } catch (failure) {
      failureMessage = message(failure);
      notice(failureMessage);
      if (statusElement) statusElement.textContent = failureMessage;
    }
    finally {
      if (statusElement) {
        statusElement.hidden = !failureMessage;
        statusElement.dataset.loading = 'false';
        statusElement.dataset.error = String(Boolean(failureMessage));
      }
      setBusy(false);
      icons();
    }
  }
  function updateLanguageText() {
    document.documentElement.lang = state.language;
    const titleKey = document.body.dataset.servicePage === 'compatibility'
      ? 'compatibilityPageTitle'
      : document.body.classList.contains('astrology-catalogue') ? 'astrologyHubTitle'
        : document.body.classList.contains('services-hub') ? 'servicesHubTitle' : 'appTitle';
    document.title = `${t(titleKey)} | RightConnect`;
    document.querySelectorAll('[data-i18n]').forEach(element => { element.textContent = t(element.dataset.i18n); });
    document.querySelectorAll('[data-i18n-aria]').forEach(element => { element.setAttribute('aria-label', t(element.dataset.i18nAria)); });
    $('#account-status').textContent = t(state.session ? 'signedIn' : 'guest');
  }
  async function loadServices() {
    $('#catalogue-status').hidden = false;
    $('#catalogue-status').textContent = t('loadingServices');
    $('#reload-services').hidden = true;
    state.catalogueError = null;
    try {
      const result = await request('/services');
      if (!Array.isArray(result.services) || typeof result.ai_available !== 'boolean') throw error('invalidResponse');
      state.services = result.services;
      state.aiAvailable = result.ai_available;
    } catch (failure) {
      state.catalogueError = error('catalogueUnavailable');
      state.services = [];
      state.aiAvailable = false;
    }
    renderCatalogue();
    const pageService = document.body.dataset.servicePage;
    if (pageService) {
      const descriptor = descriptors.find(item => item.key === pageService);
      if (descriptor) {
        selectService(descriptor);
        const service = state.services.find(item => item.key === pageService);
        const reasons = service && Array.isArray(service.unavailable_reasons) ? service.unavailable_reasons : [];
        const labels = { feature_disabled: 'featureDisabled', ai_provider_missing: 'providerMissing', rate_limit_secret_missing: 'rateSaltMissing', ephemeris_missing: 'ephemerisMissing' };
        notice(state.catalogueError ? t('catalogueUnavailable') : reasons.length
          ? reasons.map(reason => t(labels[reason] || 'unavailable')).join(' ')
          : !state.aiAvailable ? t('aiUnavailable') : '');
      }
    }
  }
  function renderCatalogue() {
    const grid = $('#service-grid');
    grid.replaceChildren();
    const catalogueStatus = $('#catalogue-status');
    catalogueStatus.textContent = '';
    catalogueStatus.hidden = true;
    $('#reload-services').hidden = true;
    for (const [index, descriptor] of descriptors.entries()) {
      const service = state.services.find(item => item.key === descriptor.key);
      // Compatibility is calculated in the browser and does not need the AI report API.
      // Marriage matching and horoscope are calculated by /api/v1/porutham, not the AI report API.
      const available = ['compatibility', 'horoscope'].includes(descriptor.key) || Boolean(state.aiAvailable && service && service.available === true);
      const card = text('a', undefined, 'service-card');
      card.href = `/pages/${descriptor.page}`;
      const symbol = text('span', undefined, 'service-icon');
      symbol.setAttribute('aria-hidden', 'true');
      const icon = text('i');
      icon.dataset.lucide = descriptor.icon;
      symbol.append(icon, text('span', String(index + 1).padStart(2, '0'), 'icon-fallback'));
      card.append(symbol, text('span', titleFor(descriptor), 'service-title'));
      card.append(text('span', service && service[`description_${state.language}`] || descriptor[state.language][1], 'service-description'));
      if (!available) card.append(text('span', t('comingSoon'), 'unavailable'));
      grid.append(card);
    }
    icons();
  }
  function makeField(parent, { name, label, type = 'text', value = '', required = true, help, min, max, step, maxLength, options }) {
    const wrapper = text('div', undefined, 'field');
    const id = `ai-${name.replace(/[^a-z0-9-]/gi, '-')}`;
    const caption = text('label', t(label));
    caption.htmlFor = id;
    const control = document.createElement(options ? 'select' : 'input');
    control.id = id;
    control.name = name;
    control.required = required;
    if (!options) control.type = type;
    if (options) for (const [optionValue, optionLabel] of options) {
      const option = text('option', optionLabel);
      option.value = String(optionValue);
      control.append(option);
    }
    control.value = String(value);
    if (min !== undefined) control.min = String(min);
    if (max !== undefined) control.max = String(max);
    if (step !== undefined) control.step = String(step);
    if (maxLength) control.maxLength = maxLength;
    control.autocomplete = 'off';
    wrapper.append(caption, control);
    if (help) {
      const hint = text('small', t(help));
      hint.id = `${id}-help`;
      control.setAttribute('aria-describedby', hint.id);
      wrapper.append(hint);
    }
    parent.append(wrapper);
    control.addEventListener('input', () => control.setCustomValidity(''));
    return control;
  }
  function check(parent, name, label) {
    const wrapper = text('label', undefined, 'check-label');
    const input = document.createElement('input');
    input.type = 'checkbox';
    input.name = name;
    input.required = true;
    wrapper.append(input, text('span', t(label)));
    parent.append(wrapper);
    return input;
  }
  function today() {
    const current = new Date();
    return `${current.getFullYear()}-${String(current.getMonth() + 1).padStart(2, '0')}-${String(current.getDate()).padStart(2, '0')}`;
  }
  function birthGroup(parent, prefix, heading, details = {}, allowSaved = true) {
    const compatibility = state.selected && state.selected.key === 'compatibility';
    const detailedKattam = compatibility && ((state.compatibilityStep === 'kattam' && (prefix === 'bride' || prefix === 'groom'))
      || (state.compatibilityStep === 'jathagam' && prefix === 'person'));
    const group = document.createElement('fieldset');
    group.dataset.birth = prefix;
    group.append(text('legend', t(heading)));
    const controls = {};
    if (state.session && allowSaved && !compatibility) {
      const pickerWrap = text('div', undefined, 'saved-picker');
      const picker = makeField(pickerWrap, {
        name: `${prefix}-member`, label: 'savedMember', required: false,
        options: [['', t('manualMember')], ...state.members.map(member => [member.id, member.label])]
      });
      group.append(pickerWrap);
      picker.addEventListener('change', () => {
        const member = state.members.find(item => item.id === picker.value);
        for (const [key, control] of Object.entries(controls)) control.value = member && member.details[key] !== undefined ? member.details[key] : key === 'timezone' ? 'Asia/Kolkata' : '';
        if (preset) preset.value = '';
        if (confirmation) confirmation.checked = false;
      });
    }
    const grid = text('div', undefined, 'field-grid');
    const definitions = [
      ['name', 'name', 'text', { required: false, maxLength: 100 }],
      ['birth_date', 'birthDate', 'date', { min: '1900-01-01', max: today() }],
      ['birth_time', 'birthTime', 'time', { help: 'localTime', step: 1 }]
    ];
    for (const [key, label, type, extras] of definitions) controls[key] = makeField(grid, { name: `${prefix}.${key}`, label, type, value: details[key] || '', ...extras });
    if (compatibility) controls.name.placeholder = t(prefix === 'bride' ? 'brideDefaultName' : 'groomDefaultName');
    let preset = null;
    const confirmation = null;
    if (detailedKattam) {
      controls.place = makeField(grid, { name: `${prefix}.place`, label: 'birthCityOptional', value: details.place || '', maxLength: 160, required: false, help: 'kattamPlaceHelp' });
      const suggestions = document.createElement('datalist');
      suggestions.id = `ai-${prefix}-city-list`;
      for (const city of cities) {
        const option = document.createElement('option');
        option.value = state.language === 'ta' ? city[1] : city[0];
        suggestions.append(option);
      }
      controls.place.setAttribute('list', suggestions.id);
      grid.append(suggestions);
      group.append(grid);
      parent.append(group);
      return;
    }
    preset = makeField(grid, { name: `${prefix}-city`, label: 'cityPreset', required: false, options: [['', t('manualCity')], ...cities.map(city => [city[0], state.language === 'ta' ? city[1] : city[0]])] });
    controls.place = makeField(grid, { name: `${prefix}.place`, label: 'place', value: details.place || '', maxLength: 160 });
    controls.place.minLength = 2;
    if (!compatibility) {
      controls.latitude = makeField(grid, { name: `${prefix}.latitude`, label: 'latitude', type: 'number', min: -90, max: 90, step: 'any', value: details.latitude === undefined ? '' : details.latitude });
      controls.longitude = makeField(grid, { name: `${prefix}.longitude`, label: 'longitude', type: 'number', min: -180, max: 180, step: 'any', value: details.longitude === undefined ? '' : details.longitude });
    }
    controls.timezone = makeField(grid, { name: `${prefix}.timezone`, label: 'timezone', value: details.timezone || 'Asia/Kolkata', maxLength: 80, help: 'timezoneHelp' });
    group.append(grid, text('p', t(compatibility ? 'compatibilityPlaceHelp' : 'locationHelp'), 'form-help'));
    for (const key of compatibility ? ['place', 'timezone'] : ['place', 'latitude', 'longitude', 'timezone']) controls[key].addEventListener('input', () => { if (confirmation) confirmation.checked = false; preset.value = ''; });
    preset.addEventListener('change', () => {
      const city = cities.find(item => item[0] === preset.value);
      if (city) {
        controls.place.value = state.language === 'ta' ? city[1] : city[0];
        if (controls.latitude) controls.latitude.value = city[2];
        if (controls.longitude) controls.longitude.value = city[3];
        controls.timezone.value = city[4];
      } else {
        controls.place.value = '';
        if (controls.latitude) controls.latitude.value = '';
        if (controls.longitude) controls.longitude.value = '';
        controls.timezone.value = 'Asia/Kolkata';
      }
      if (confirmation) confirmation.checked = false;
    });
    parent.append(group);
  }
  const normalisePlace = value => String(value || '').toLowerCase().replace(/[\s.,()-]/g, '');
  // No geocoding: a typed place resolves only against the city list and its aliases.
  function findCity(place) {
    const key = normalisePlace(place);
    if (!key) return null;
    const names = city => [city[0], city[1], ...(city[5] || [])].map(normalisePlace);
    return cities.find(city => names(city).includes(key))
      || cities.find(city => names(city).some(name => name.length >= 4 && key.includes(name)))
      || null;
  }
  function getKattamBirth(form, prefix, fallbackName) {
    const value = key => form.elements.namedItem(`${prefix}.${key}`).value.trim();
    const typed = value('place');
    const city = findCity(typed);
    const used = city || cities[0];
    return {
      name: value('name') || fallbackName, birth_date: value('birth_date'), birth_time: value('birth_time'),
      place: typed, place_status: city ? 'ok' : typed ? 'unknown' : 'missing',
      latitude: used[2], longitude: used[3], timezone: used[4]
    };
  }
  function getBirth(form, prefix, { coordinates = true, fallbackName = '' } = {}) {
    const value = key => form.elements.namedItem(`${prefix}.${key}`).value.trim();
    const birth = { name: value('name') || fallbackName, birth_date: value('birth_date'), birth_time: value('birth_time'), place: value('place'), timezone: value('timezone') };
    if (coordinates) {
      const coordinate = key => value(key) === '' ? '' : Number(value(key));
      birth.latitude = coordinate('latitude');
      birth.longitude = coordinate('longitude');
    }
    return birth;
  }
  function validateForm(form) {
    for (const input of form.querySelectorAll('input, select')) {
      input.setCustomValidity('');
      if (input.validity.valueMissing || (input.required && input.type !== 'checkbox' && !input.value.trim())) input.setCustomValidity(t(input.type === 'checkbox' ? 'requiredConsent' : 'requiredField'));
      else if (!input.validity.valid) input.setCustomValidity(t(input.type === 'number' ? 'invalidNumber' : 'invalidField'));
    }
    for (const input of form.querySelectorAll('input[type="date"]')) {
      if (input.value && (input.value < '1900-01-01' || input.value > today())) input.setCustomValidity(t('dateError'));
    }
    for (const input of form.querySelectorAll('input[name$=".timezone"]')) {
      try { new Intl.DateTimeFormat('en', { timeZone: input.value.trim() }).format(); }
      catch (_) { input.setCustomValidity(t('invalidTimezone')); }
    }
    const fullName = form.elements.namedItem('full_name');
    if (fullName && !/^[A-Za-z]+(?: [A-Za-z]+)*$/.test(fullName.value.trim().replace(/\s+/g, ' '))) fullName.setCustomValidity(t('englishNameError'));
    return form.reportValidity();
  }
  function readInputs(form, descriptor) {
    if (descriptor.key === 'compatibility' && state.compatibilityStep === 'jathagam') return {
      person: getKattamBirth(form, 'person', state.language === 'ta' ? 'ஜாதகர்' : 'Native')
    };
    if (descriptor.key === 'compatibility') return {
      bride: getKattamBirth(form, 'bride', 'பெண்'),
      groom: getKattamBirth(form, 'groom', 'பையன்')
    };
    if (descriptor.key === 'numerology') return { full_name: form.elements.namedItem('full_name').value.trim(), birth_date: form.elements.namedItem('birth_date').value };
    if (descriptor.key === 'vastu') return Object.fromEntries(['facing', 'main_door', 'kitchen', 'bedroom'].map(key => [key, form.elements.namedItem(key).value]));
    if (descriptor.key === 'forecast') return { rasi: Number(form.elements.namedItem('rasi').value), period: form.elements.namedItem('period').value };
    const birth = getBirth(form, 'birth');
    return descriptor.key === 'baby-names' ? { ...birth, gender: form.elements.namedItem('gender').value } : birth;
  }
  function selectService(descriptor, inputs = {}) {
    if (state.busy) return;
    state.selected = descriptor;
    state.report = null;
    state.inputs = inputs;
    if (descriptor.key === 'compatibility' && !state.quickMatch) state.compatibilityStep = 'choose';
    state.reportVersion += 1;
    notice('');
    $('#report-panel').hidden = true;
    $('#catalogue').hidden = true;
    renderSelectedInput(inputs);
    focusHeading('#form-title');
  }
  function renderSelectedInput(inputs = {}) {
    if (state.selected && state.selected.key === 'compatibility' && state.compatibilityStep === 'choose') {
      renderCompatibilityChoice();
      return;
    }
    if (state.selected && state.selected.key === 'compatibility' && state.compatibilityStep === 'rasi') {
      renderQuickMatchForm(inputs);
      return;
    }
    renderInput(inputs);
  }

  function readQuickMatch(form) {
    const pick = name => {
      const value = form.elements.namedItem(name).value;
      return value === '' ? '' : Number(value);
    };
    const person = role => ({
      name: form.elements.namedItem(`${role}.name`).value.trim(),
      rasi: pick(`${role}.rasi`),
      nakshatra: pick(`${role}.nakshatra`)
    });
    return { bride: person('bride'), groom: person('groom') };
  }

  // Each Rasi spans nine padas; lists the stars (and their padas) inside it for the picker.
  function starsForRasi(rasi) {
    const stars = [];
    for (let star = 0; star < 27; star += 1) {
      const padas = [1, 2, 3, 4].filter(pada => Math.floor((star * 4 + pada - 1) / 9) === rasi);
      if (padas.length) stars.push({ star, padas });
    }
    return stars;
  }

  function fillStarOptions(select, rasi, selected) {
    select.replaceChildren();
    const placeholder = text('option', t(rasi === '' ? 'selectRasiFirst' : 'selectStar'));
    placeholder.value = '';
    select.append(placeholder);
    select.disabled = rasi === '';
    if (rasi === '') return;
    for (const { star, padas } of starsForRasi(Number(rasi))) {
      const suffix = padas.length < 4 ? ` (${padas.join(', ')} ${t('padaSuffix')})` : '';
      const option = text('option', `${nakshatras[state.language][star]}${suffix}`);
      option.value = String(star);
      select.append(option);
    }
    select.value = [...select.options].some(option => option.value === String(selected)) ? String(selected) : '';
  }

  function captureSelectedInputs() {
    if (!state.selected) return state.inputs;
    if (state.selected.key === 'compatibility' && state.compatibilityStep === 'choose') return state.inputs;
    if (state.selected.key === 'compatibility' && state.compatibilityStep === 'rasi') {
      if (!state.quickMatch && $('#input-panel form')) state.inputs = readQuickMatch($('#input-panel form'));
      else if (state.quickInputs) state.inputs = state.quickInputs;
      return state.inputs;
    }
    if (!$('#input-panel form')) return state.inputs;
    state.inputs = readInputs($('#input-panel form'), state.selected);
    return state.inputs;
  }

  function rerenderSelectedInput() {
    if (state.selected && state.selected.key === 'compatibility' && state.compatibilityStep === 'rasi' && state.quickMatch) {
      renderQuickMatchResults();
      return;
    }
    renderSelectedInput(state.inputs || {});
  }

  function showCompatibilityChoice() {
    $('#report-panel').hidden = true;
    state.compatibilityStep = 'choose';
    renderCompatibilityChoice();
    focusHeading('#form-title');
  }

  function backFromKattam() {
    if (state.kattamFrom === 'rasi' && state.quickMatch) {
      $('#report-panel').hidden = true;
      state.compatibilityStep = 'rasi';
      renderQuickMatchResults();
      focusHeading('#form-title');
    } else {
      showCompatibilityChoice();
    }
  }

  function renderCompatibilityChoice() {
    const panel = $('#input-panel');
    panel.replaceChildren();
    panel.hidden = false;
    $('#report-panel').hidden = true;
    $('#catalogue').hidden = true;
    const top = text('div', undefined, 'panel-top');
    const heading = text('h2', t('chooseTitle'));
    heading.id = 'form-title';
    top.append(heading, button(t('back'), showCatalogue, 'quiet', 'arrow-left'));
    panel.append(top);
    const grid = text('div', undefined, 'service-grid match-choice');
    const options = [
      ['chooseRasiTitle', 'chooseRasiHelp', 'star', () => {
        state.compatibilityStep = 'rasi';
        state.quickMatch = null;
        renderQuickMatchForm(state.quickInputs || {});
        focusHeading('#form-title');
      }],
      ['chooseKattamTitle', 'chooseKattamHelp', 'layout-grid', () => openReportForm('kattam')],
      ['chooseJathagamTitle', 'chooseJathagamHelp', 'sun', () => openReportForm('jathagam')]
    ];
    options.forEach(([title, help, iconName, action], index) => {
      const card = text('button', undefined, 'service-card');
      card.type = 'button';
      const symbol = text('span', undefined, 'service-icon');
      symbol.setAttribute('aria-hidden', 'true');
      const icon = text('i');
      icon.dataset.lucide = iconName;
      symbol.append(icon, text('span', String(index + 1), 'icon-fallback'));
      card.append(symbol, text('span', t(title), 'service-title'), text('span', t(help).replace('{price}', priceLabel()), 'service-description'));
      card.addEventListener('click', action);
      grid.append(card);
    });
    panel.append(grid);
    icons();
  }

  function openReportForm(kind) {
    state.compatibilityStep = kind;
    state.kattamFrom = 'choose';
    const last = state.account && state.account.last_inputs ? state.account.last_inputs[kind] : null;
    state.inputs = state.kattam && state.kattam.kind === kind ? state.kattam.inputs : last || {};
    renderInput(state.inputs);
    focusHeading('#form-title');
  }
  const lockedKey = key => (state.kattam && state.kattam.kind === 'jathagam' ? `${key}Jathagam` : key);

  function renderQuickMatchForm(values = {}) {
    const panel = $('#input-panel');
    panel.replaceChildren();
    panel.hidden = false;
    $('#report-panel').hidden = true;
    $('#catalogue').hidden = true;
    const top = text('div', undefined, 'panel-top');
    const heading = text('h2', t('rasiStepTitle'));
    heading.id = 'form-title';
    top.append(heading, button(t('backToChoice'), showCompatibilityChoice, 'quiet', 'arrow-left'));
    panel.append(top, text('p', t('rasiStepHelp'), 'form-help'));

    const form = document.createElement('form');
    form.noValidate = true;
    const pairs = [
      ['bride', t('brideName'), t('brideRasi'), t('brideStar')],
      ['groom', t('groomName'), t('groomRasi'), t('groomStar')]
    ];
    for (const [role, nameLabel, rasiLabel, starLabel] of pairs) {
      const saved = values[role] || {};
      const group = document.createElement('fieldset');
      group.append(text('legend', t(`${role}Heading`)));
      const fields = text('div', undefined, 'field-grid quick-match-grid');
      makeField(fields, { name: `${role}.name`, label: nameLabel, required: false, maxLength: 100, value: saved.name || '' });
      const rasiOptions = [['', t('selectRasi')], ...rasis[state.language].map((name, index) => [index, name])];
      const rasiValue = saved.rasi === undefined ? '' : saved.rasi;
      const rasiSelect = makeField(fields, { name: `${role}.rasi`, label: rasiLabel, options: rasiOptions, value: rasiValue });
      const starSelect = makeField(fields, { name: `${role}.nakshatra`, label: starLabel, options: [] });
      fillStarOptions(starSelect, String(rasiValue), saved.nakshatra === undefined ? '' : saved.nakshatra);
      rasiSelect.addEventListener('change', () => fillStarOptions(starSelect, rasiSelect.value, ''));
      group.append(fields);
      form.append(group);
    }
    const submit = text('button', t('checkRasiMatch'), 'button');
    submit.type = 'submit';
    submit.dataset.lock = '';
    const actions = text('div', undefined, 'form-actions');
    actions.append(submit);
    const status = text('p', '', 'inline-status');
    status.setAttribute('role', 'status');
    status.hidden = true;
    form.append(actions, status);
    form.addEventListener('submit', event => {
      event.preventDefault();
      if (state.busy || !validateForm(form)) return;
      const inputs = readQuickMatch(form);
      if (!inputs.bride.name) inputs.bride.name = 'பெண்';
      if (!inputs.groom.name) inputs.groom.name = 'பையன்';
      state.quickInputs = inputs;
      perform(async () => {
        state.quickMatch = await porutham('/rasi', { language: state.language, ...inputs });
        renderQuickMatchResults();
        focusHeading('#form-title');
      }, status, 'calculating');
    });
    panel.append(form);
    icons();
  }

  function renderQuickMatchResults() {
    const panel = $('#input-panel');
    panel.replaceChildren();
    panel.hidden = false;
    const data = state.quickMatch;
    if (!data) return;
    const top = text('div', undefined, 'panel-top');
    const heading = text('h2', data.title);
    heading.id = 'form-title';
    top.append(heading, button(t('editRasi'), () => { state.quickMatch = null; renderQuickMatchForm(state.quickInputs); }, 'quiet', 'arrow-left'));
    const verdict = text('div', undefined, `match-verdict level-${data.level}`);
    verdict.setAttribute('role', 'status');
    verdict.append(text('strong', data.verdict), text('span', data.names.join(' · ')));
    const body = text('div', undefined, 'kattam-report');
    data.blocks.forEach(block => body.append(renderBlock(block)));
    const actions = text('div', undefined, 'form-actions match-actions');
    actions.append(button(t('viewKattam'), () => {
      state.compatibilityStep = 'kattam';
      state.kattamFrom = 'rasi';
      const inputs = { bride: { name: state.quickInputs.bride.name }, groom: { name: state.quickInputs.groom.name } };
      state.inputs = inputs;
      renderInput(inputs);
      focusHeading('#form-title');
    }, ''));
    panel.append(top, verdict, body, text('p', data.disclaimer, 'form-help'), actions);
    icons();
  }

  async function porutham(path, body, method = 'POST') {
    const headers = { Accept: 'application/json' };
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (state.session) headers.Authorization = `Bearer ${state.session.access_token}`;
    let response;
    try {
      response = await fetch(`/api/v1/porutham${path}`, {
        method, headers, body: body === undefined ? undefined : JSON.stringify(body), cache: 'no-store', credentials: 'omit'
      });
    } catch (_) { throw error('networkError'); }
    if (!response.ok) {
      const problem = await response.json().catch(() => ({}));
      if (response.status === 422 && /time/.test(String(problem.detail))) throw error('kattamTimeError');
      throw error({ 400: /^\/(kattam|pack)\//.test(path) ? 'payVerifyError' : 'invalidError', 401: 'authError', 402: 'noCreditsError', 404: 'missingError',
        422: 'invalidError', 429: 'rateError', 503: 'payUnavailable' }[response.status] || 'unavailableError');
    }
    if (response.status === 204) return null;
    try { return await response.json(); } catch (_) { throw error('invalidResponse'); }
  }

  const SOUTH_INDIAN_CELLS = { 11: [1, 1], 0: [1, 2], 1: [1, 3], 2: [1, 4], 3: [2, 4], 4: [3, 4], 5: [4, 4], 6: [4, 3], 7: [4, 2], 8: [4, 1], 9: [3, 1], 10: [2, 1] };
  const FILLER = {
    ta: 'ஜாதகம் பொருத்தம் கிரகம் தசை புத்தி லக்னம் ராசி வீடு பலன் காலம் நன்மை கவனம் இருவருக்கும் நட்சத்திரம் அதிபதி சுபம்',
    en: 'chart match planet dasa bhukti lagna rasi house result period good care both star lord period'
  };
  let fillerIndex = 0;
  // The server sends only the length of paid text; the page shows blurred filler of that length.
  function blurred(tag, length, className = '') {
    const words = (FILLER[state.language] || FILLER.ta).split(' ');
    let value = '';
    while (value.length < length) value += `${words[fillerIndex++ % words.length]} `;
    const node = text(tag, value.slice(0, length).trim(), `${className} is-blurred`.trim());
    node.setAttribute('aria-hidden', 'true');
    return node;
  }
  function renderBlock(block) {
    const fragment = document.createDocumentFragment();
    const paragraphClass = { note: 'kattam-note', help: 'form-help', lead: 'kattam-lead' }[block.type];
    if (paragraphClass) {
      if (block.hidden) block.hidden.forEach(length => fragment.append(blurred('p', length, paragraphClass)));
      else fragment.append(text('p', block.text, paragraphClass));
    } else if (block.type === 'person') {
      fragment.append(text('h4', block.text, 'kattam-person'));
    } else if (block.type === 'subheading') {
      fragment.append(text('h3', block.text, 'kattam-heading kattam-subheading'));
    } else if (block.type === 'notice') {
      const box = text('div', undefined, 'notice');
      if (block.title) box.append(text('strong', block.title));
      block.lines.forEach(line => box.append(text('p', line)));
      fragment.append(box);
    } else if (block.type === 'items') {
      fragment.append(renderItems(block));
    } else if (block.type === 'table') {
      fragment.append(renderTable(block));
    } else if (block.type === 'summary') {
      const box = text('div', undefined, `kattam-summary level-${block.level}`);
      block.lines.forEach(line => box.append(text('p', line)));
      (block.hidden || []).forEach(length => box.append(blurred('p', length)));
      fragment.append(box);
    } else if (block.type === 'charts') {
      fragment.append(renderCharts(block));
    }
    return fragment;
  }
  function renderItems(block) {
    const list = text(block.ordered ? 'ol' : 'ul', undefined, 'match-results');
    for (const entry of block.items) {
      const item = text('li', undefined, `match-result tone-${entry.tone}`);
      if (entry.title === null) item.append(blurred('strong', 24), blurred('span', 10, 'match-status'));
      else item.append(text('strong', entry.title), text('span', entry.badge, 'match-status'));
      entry.paragraphs.forEach(paragraph => item.append(text('p', paragraph)));
      (entry.hidden || []).forEach(length => item.append(blurred('p', length)));
      if (entry.small) item.append(text('small', entry.small));
      list.append(item);
    }
    return list;
  }
  function renderTable(block) {
    const table = text('table', undefined, block.kind === 'profile' ? 'match-profile' : `match-profile kattam-table${block.kind === 'timeline' ? ' kattam-timeline' : ''}`);
    if (block.caption) table.append(text('caption', block.caption));
    const head = text('tr');
    block.head.forEach(label => {
      const cell = text('th', label);
      cell.scope = 'col';
      head.append(cell);
    });
    const thead = text('thead');
    thead.append(head);
    const tbody = text('tbody');
    for (const row of block.rows) {
      const line = text('tr');
      row.forEach((value, index) => {
        const tag = index === 0 ? 'th' : 'td';
        const cell = value.hidden ? blurred(tag, Math.min(value.hidden, 48)) : text(tag, value.text);
        if (index === 0) cell.scope = 'row';
        if (value.tone) cell.classList.add(`tone-${value.tone}`);
        line.append(cell);
      });
      tbody.append(line);
    }
    table.append(thead, tbody);
    const scroller = text('div', undefined, 'kattam-table-scroll');
    scroller.append(table);
    return scroller;
  }
  function renderCharts(block) {
    const wrap = text('div', undefined, 'kattam-charts');
    for (const chart of block.charts) {
      const figure = text('figure', undefined, 'kattam-figure');
      const grid = text('div', undefined, 'kattam-grid');
      for (let sign = 0; sign < 12; sign += 1) {
        const data = chart.cells && chart.cells[sign];
        const cell = text('div', undefined, 'kattam-cell');
        [cell.style.gridRow, cell.style.gridColumn] = SOUTH_INDIAN_CELLS[sign].map(String);
        if (data) {
          cell.append(text('small', data.name, 'kattam-sign'));
          if (data.planets) cell.append(text('span', data.planets, 'kattam-planets'));
          if (data.lagna) cell.classList.add('is-lagna');
        } else {
          cell.append(blurred('span', 4 + (sign * 5) % 8, 'kattam-planets'));
        }
        grid.append(cell);
      }
      const [owner, kind] = chart.title.split(' — ');
      const center = text('div', undefined, 'kattam-center');
      center.append(text('strong', owner), text('span', kind || ''));
      grid.append(center);
      if (chart.cells) {
        grid.setAttribute('role', 'img');
        grid.setAttribute('aria-label', `${chart.title}: ${chart.cells.filter(cell => cell.planets).map(cell => `${cell.name}: ${cell.planets}`).join('; ')}`);
      }
      figure.append(grid, text('figcaption', chart.title));
      wrap.append(figure);
    }
    return wrap;
  }
  function focusHeading(selector) {
    const heading = $(selector);
    if (!heading) return;
    heading.tabIndex = -1;
    heading.focus({ preventScroll: true });
    heading.scrollIntoView({ block: 'start', behavior: 'auto' });
  }
  function renderInput(inputs = {}) {
    const descriptor = state.selected;
    if (!descriptor) return;
    const panel = $('#input-panel');
    panel.replaceChildren();
    panel.hidden = false;
    const top = text('div', undefined, 'panel-top');
    const jathagam = descriptor.key === 'compatibility' && state.compatibilityStep === 'jathagam';
    const heading = text('h2', descriptor.key === 'compatibility' ? t(jathagam ? 'jathagamStepTitle' : 'kattamStepTitle') : titleFor(descriptor));
    heading.id = 'form-title';
    top.append(heading, descriptor.key === 'compatibility'
      ? button(t(!jathagam && state.kattamFrom === 'rasi' && state.quickMatch ? 'backToRasi' : 'backToChoice'), backFromKattam, 'quiet', 'arrow-left')
      : button(t('back'), showCatalogue, 'quiet', 'arrow-left'));
    panel.append(top);
    const form = document.createElement('form');
    form.noValidate = true;
    const editable = document.createElement('fieldset');
    editable.dataset.lock = '';
    if (jathagam) {
      birthGroup(editable, 'person', 'jathagamPerson', inputs.person || {});
    } else if (descriptor.key === 'compatibility') {
      birthGroup(editable, 'bride', 'bride', inputs.bride || {});
      birthGroup(editable, 'groom', 'groom', inputs.groom || {});
    } else if (['horoscope', 'gemstone', 'baby-names'].includes(descriptor.key)) {
      birthGroup(editable, 'birth', 'birth', inputs);
      if (descriptor.key === 'baby-names') makeField(editable, { name: 'gender', label: 'gender', value: inputs.gender || 'neutral', options: ['neutral', 'male', 'female'].map(key => [key, t(key)]) });
    } else {
      const grid = text('div', undefined, 'field-grid');
      if (descriptor.key === 'numerology') {
        makeField(grid, { name: 'full_name', label: 'fullName', value: inputs.full_name || '', maxLength: 100, help: 'englishNameHelp' });
        makeField(grid, { name: 'birth_date', label: 'birthDate', type: 'date', value: inputs.birth_date || '', min: '1900-01-01', max: today() });
      } else if (descriptor.key === 'vastu') {
        for (const key of ['facing', 'main_door', 'kitchen', 'bedroom']) makeField(grid, { name: key, label: key, value: inputs[key] || 'N', options: ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'].map(direction => [direction, t(direction)]) });
      } else if (descriptor.key === 'forecast') {
        makeField(grid, { name: 'rasi', label: 'rasi', value: inputs.rasi === undefined ? 0 : inputs.rasi, options: rasis[state.language].map((name, index) => [index, name]) });
        makeField(grid, { name: 'period', label: 'period', value: inputs.period || 'daily', options: ['daily', 'weekly'].map(key => [key, t(key)]) });
      }
      editable.append(grid);
      if (descriptor.key === 'vastu') editable.append(text('p', t('directionHelp'), 'form-help'));
    }
    if (descriptor.key === 'compatibility') editable.append(text('p', t('kattamPrivacy'), 'form-help'));
    else check(editable, 'report-consent', 'reportConsent');
    const submit = text('button', t(jathagam ? 'jathagamGenerate' : descriptor.key === 'compatibility' ? 'kattamGenerate' : 'generate'), 'button');
    submit.type = 'submit';
    submit.dataset.lock = '';
    const actions = text('div', undefined, 'form-actions');
    actions.append(submit);
    editable.append(actions);
    const status = text('p', '', 'inline-status');
    status.setAttribute('role', 'status');
    status.hidden = true;
    form.append(editable, status);
    form.addEventListener('submit', async event => {
      event.preventDefault();
      if (state.busy || !validateForm(form)) return;
      const inputs = readInputs(form, descriptor);
      if (descriptor.key === 'compatibility') {
        state.inputs = inputs;
        const kind = jathagam ? 'jathagam' : 'kattam';
        const selected = !jathagam && state.kattamFrom === 'rasi' && state.quickInputs ? { bride: state.quickInputs.bride, groom: state.quickInputs.groom } : null;
        const kattam = { kind, inputs, selected, hash: await kattamHash(kind, inputs), report: null };
        perform(async () => {
          await loadKattam(kattam);
          state.kattam = kattam;
          state.kattamPending = null;
          state.kattamPayMessage = '';
          renderKattamReport();
          focusHeading('#report-heading');
          if (state.session) loadAccount();
        }, status, 'calculating');
        return;
      }
      perform(async () => {
        const token = newToken();
        const version = state.reportVersion;
        const result = await request(`/${descriptor.key}`, { method: 'POST', token, body: { inputs, language: state.language, tier: 'basic', consent: true } });
        if (!validReport(result)) throw error('invalidResponse');
        keepCapability(result.id, token);
        if (version !== state.reportVersion) return;
        state.inputs = inputs;
        acceptReport(result);
      }, status, 'generating');
    });
    panel.append(form);
    icons();
  }
  function showCatalogue() {
    if (state.busy) return;
    if (document.body.dataset.servicePage) {
      location.href = '/pages/services.html';
      return;
    }
    state.selected = null;
    state.inputs = null;
    state.report = null;
    state.quickMatch = null;
    state.quickInputs = null;
    state.compatibilityStep = 'choose';
    state.kattamFrom = null;
    state.reportVersion += 1;
    $('#input-panel').replaceChildren();
    $('#input-panel').hidden = true;
    $('#report-panel').replaceChildren();
    $('#report-panel').hidden = true;
    $('#catalogue').hidden = false;
    notice('');
    focusHeading('#catalogue-heading');
  }
  function acceptReport(result) {
    state.report = result;
    $('#input-panel').hidden = true;
    $('#catalogue').hidden = true;
    renderReport();
    focusHeading('#report-heading');
  }
  function reportText() {
    const report = state.report;
    const written = report && report.report;
    if (!written) return '';
    const sections = Array.isArray(written.sections) ? written.sections : [];
    return [written.title, ...sections.map(section => `${section.heading}\n\n${section.body}`), written.disclaimer, t('tradition')].filter(Boolean).join('\n\n');
  }
  function renderReport() {
    const panel = $('#report-panel');
    panel.replaceChildren();
    panel.hidden = false;
    const report = state.report;
    if (!report) return;
    const top = text('div', undefined, 'panel-top');
    const heading = text('h2', report.report && report.report.title || t('reportTitle'));
    heading.id = 'report-heading';
    top.append(heading, button(t('back'), showCatalogue, 'quiet', 'arrow-left'));
    panel.append(top, text('p', `${t(report.status)} · ${dateLabel(report.created_at)}`, 'report-meta'));
    const operationStatus = text('p', '', 'inline-status');
    operationStatus.setAttribute('role', 'status');
    operationStatus.hidden = true;
    panel.append(operationStatus);
    if (report.status === 'completed' && report.report && Array.isArray(report.report.sections)) {
      const body = text('article', undefined, 'report-body');
      body.lang = report.language === 'en' ? 'en' : 'ta';
      for (const section of report.report.sections) {
        const block = text('section', undefined, 'report-section');
        block.append(text('h3', section.heading), text('p', section.body));
        body.append(block);
      }
      body.append(text('p', report.report.disclaimer, 'report-disclaimer'));
      panel.append(body);
    } else {
      panel.append(text('p', t(report.status === 'pending' ? 'pendingHelp' : 'failedHelp'), 'notice'));
    }
    const actions = text('div', undefined, 'report-actions');
    if (report.status === 'failed') actions.append(button(t('retry'), () => changeReport('retry', state.language, operationStatus), '', 'rotate-ccw'));
    if (report.status === 'pending') actions.append(button(t('refresh'), () => openReport(report.id), '', 'refresh-cw'));
    if (report.status === 'completed' && report.report) {
      actions.append(button(t('copy'), () => perform(async () => {
        try { await navigator.clipboard.writeText(reportText()); notice(t('copied')); }
        catch (_) { throw error('copyError'); }
      }), 'secondary', 'copy'));
      actions.append(button(t('download'), downloadReport, 'secondary', 'download'));
      if (navigator.share) actions.append(button(t('share'), () => perform(async () => {
        try { await navigator.share({ title: String(state.report.report.title || t('reportTitle')), text: reportText() }); }
        catch (failure) { if (failure.name !== 'AbortError') throw error('shareError'); }
      }), 'secondary', 'share-2'));
    }
    if (descriptorFor(report.service_type)) actions.append(button(t('edit'), () => {
      const existing = state.inputs;
      selectService(descriptorFor(report.service_type), existing || {});
      if (!existing) notice(t('editUnavailable'));
    }, 'quiet', 'pencil'));
    for (const control of actions.querySelectorAll('button')) control.dataset.lock = '';
    panel.append(actions);
    if (state.storageWarning) panel.append(text('p', t('storageError'), 'notice'));
    icons();
  }
  function downloadReport() {
    const content = reportText();
    if (!content) return;
    const link = document.createElement('a');
    const url = URL.createObjectURL(new Blob(['\uFEFF', content], { type: 'text/plain;charset=utf-8' }));
    link.href = url;
    link.download = `rightconnect-report-${String(state.report.id).replace(/[^a-zA-Z0-9_-]/g, '')}.txt`;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function kattamBody(kattam) {
    const chennai = state.language === 'ta' ? cities[0][1] : cities[0][0];
    const birth = person => ({
      name: person.name, birth_date: person.birth_date, birth_time: person.birth_time, place: person.place || chennai,
      latitude: person.latitude, longitude: person.longitude, timezone: person.timezone
    });
    if (kattam.kind === 'jathagam') return { language: state.language, person: birth(kattam.inputs.person) };
    return { language: state.language, bride: birth(kattam.inputs.bride), groom: birth(kattam.inputs.groom), selected: kattam.selected };
  }
  async function loadKattam(kattam) {
    const proof = kattam.hash && state.kattamProofs[kattam.hash];
    if (proof) {
      try {
        const result = await porutham(`/${kattam.kind}/full`, { ...kattamBody(kattam), payment: proof });
        if (result.status === 'paid' && result.report) { kattam.report = result.report; return; }
      } catch (_) { /* Fall back to the preview; the buyer can pay again only if the proof is truly invalid. */ }
    }
    const result = await porutham(`/${kattam.kind}`, kattamBody(kattam));
    if (!result.report || !Array.isArray(result.report.sections)) throw error('invalidResponse');
    applyOffer(result.unlock);
    kattam.report = result.report;
    kattam.historyId = result.history_id || null;
  }
  function applyOffer(unlock) {
    if (!unlock) return;
    if (Number.isInteger(unlock.amount_paise) && unlock.amount_paise >= 100) state.kattamPrice = unlock.amount_paise;
    if (unlock.pack && Number.isInteger(unlock.pack.amount_paise)) state.packOffer = unlock.pack;
  }
  function renderPorutham(report) {
    const article = text('article', undefined, 'kattam-report');
    const verdict = text('div', undefined, `match-verdict level-${report.verdict.level}`);
    verdict.setAttribute('role', 'status');
    verdict.append(text('strong', report.verdict.headline), text('span', report.verdict.detail));
    article.append(verdict);
    if (report.alerts) article.append(renderBlock({ type: 'notice', ...report.alerts }));
    let part = null;
    for (const section of report.sections) {
      if (!section.banner && section.part !== part && report.parts[section.part]) article.append(text('h2', report.parts[section.part], 'kattam-part'));
      part = section.part;
      let target;
      if (section.key === 'expert' && !report.locked) {
        const details = text('details', undefined, 'kattam-expert');
        target = text('div', undefined, 'kattam-expert-body');
        details.append(text('summary', section.title), target);
        article.append(details);
      } else {
        target = text('section', undefined, `kattam-section${section.teaser ? ' is-locked' : ''}`);
        target.append(text(section.banner ? 'h2' : 'h3', section.title, section.banner ? 'kattam-part' : 'kattam-heading'));
        if (section.teaser) target.append(teaserLine(section.teaser));
        article.append(target);
      }
      section.blocks.forEach(block => target.append(renderBlock(block)));
      if (report.locked && section.key === report.paywall_after) article.append(paywallCard());
    }
    article.append(text('p', report.disclaimer, 'form-help kattam-disclaimer'));
    return article;
  }
  function renderKattamReport() {
    const kattam = state.kattam;
    if (!kattam || !kattam.report) return;
    const report = kattam.report;
    const paid = !report.locked;
    kattam.placeNotes = Object.values(kattam.inputs)
      .filter(person => person && person.place_status && person.place_status !== 'ok')
      .map(person => t(person.place_status === 'unknown' ? 'placeUnknown' : 'placeMissing').replace('{name}', person.name).replace('{place}', person.place));
    $('#input-panel').hidden = true;
    $('#catalogue').hidden = true;
    const panel = $('#report-panel');
    panel.replaceChildren();
    panel.hidden = false;
    const top = text('div', undefined, 'panel-top');
    const heading = text('h2', report.title);
    heading.id = 'report-heading';
    top.append(heading, button(t(state.kattamFrom === 'rasi' && state.quickMatch ? 'backToRasi' : 'backToChoice'), backFromKattam, 'quiet', 'arrow-left'));
    const editBirth = button(t('editBirth'), () => {
      if (state.kattamPaying || state.pdfBusy) return;
      panel.hidden = true;
      state.compatibilityStep = kattam.kind;
      renderInput(kattam.inputs);
      focusHeading('#form-title');
    }, 'quiet', 'pencil');
    const actions = text('div', undefined, 'report-actions');
    if (paid) {
      const pdf = button(t('downloadPdf'), downloadKattamPdf, '', 'file-down');
      pdf.dataset.pdf = '';
      actions.append(pdf, button(t('printReport'), () => window.print(), 'secondary', 'printer'), editBirth);
    } else {
      actions.append(payButton(), editBirth);
    }
    panel.append(top);
    if (!paid) panel.append(text('p', t('freePreview'), 'kattam-preview-label'));
    if (kattam.placeNotes.length) {
      const box = text('div', undefined, 'notice');
      kattam.placeNotes.forEach(note => box.append(text('p', note)));
      panel.append(box);
    }
    const article = renderPorutham(report);
    kattam.node = paid ? article : null;
    panel.append(article, actions, payStatus());
    if (!paid) panel.append(unlockBar());
    icons();
  }
  const rupees = paise => {
    const value = paise / 100;
    return `₹${Number.isInteger(value) ? value : value.toFixed(2)}`;
  };
  const priceLabel = () => rupees(state.kattamPrice);
  const hasCredits = () => Boolean(state.account && state.account.credits > 0);
  function unlockButton(className = 'kattam-teaser-unlock') {
    const credits = hasCredits();
    const control = text('button', credits ? t('useCreditShort') : t('unlockShort').replace('{price}', priceLabel()), className);
    control.type = 'button';
    control.dataset.pay = '';
    control.disabled = state.kattamPaying;
    control.addEventListener('click', credits ? useCredit : startKattamPayment);
    return control;
  }
  function teaserLine(value) {
    const line = text('p', undefined, 'kattam-teaser');
    const lock = text('i');
    lock.dataset.lucide = 'lock';
    lock.setAttribute('aria-hidden', 'true');
    line.append(lock, text('span', value), unlockButton());
    return line;
  }
  function unlockBar() {
    const bar = text('div', undefined, 'kattam-unlock-bar');
    const lock = text('i');
    lock.dataset.lucide = 'lock-open';
    lock.setAttribute('aria-hidden', 'true');
    bar.append(lock, text('span', t('unlockBar')), unlockButton('button'));
    return bar;
  }
  function paywallCard() {
    const paywall = text('section', undefined, 'kattam-paywall');
    paywall.setAttribute('aria-labelledby', 'kattam-paywall-title');
    const badge = text('span', undefined, 'kattam-paywall-icon');
    const lock = text('i');
    lock.dataset.lucide = 'lock';
    lock.setAttribute('aria-hidden', 'true');
    badge.append(lock);
    const title = text('h3', t(lockedKey('lockedTitle')));
    title.id = 'kattam-paywall-title';
    const list = text('ul', undefined, 'kattam-paywall-list');
    for (const item of t(lockedKey('lockedItems'))) list.append(text('li', item));
    paywall.append(badge, title, text('strong', hasCredits() ? t('creditsLeft').replace('{n}', state.account.credits) : priceLabel(), 'kattam-paywall-price'),
      text('p', t('lockedLead')), list, payButton(), text('small', t('payNote'), 'kattam-paywall-note'), payStatus());
    if (!hasCredits()) paywall.append(text('p', t('orPack'), 'kattam-paywall-or'), packBox());
    return paywall;
  }
  function payButton() {
    const pending = state.kattamPending && state.kattamPending.kattam === state.kattam;
    const control = pending
      ? button(t('refresh'), () => confirmKattamPayment(state.kattamPending.kattam, state.kattamPending.response), '', 'refresh-cw')
      : hasCredits() ? button(t('useCredit').replace('{n}', state.account.credits), useCredit, '', 'lock-open')
        : button(t('payUnlock').replace('{price}', priceLabel()), startKattamPayment, '', 'lock-open');
    control.dataset.pay = '';
    control.disabled = state.kattamPaying;
    return control;
  }
  function payStatus() {
    const status = text('p', state.kattamPayMessage, 'inline-status kattam-pay-status');
    status.setAttribute('role', 'status');
    status.hidden = !state.kattamPayMessage;
    return status;
  }
  function setPayStatus(value) {
    state.kattamPayMessage = value;
    document.querySelectorAll('.kattam-pay-status').forEach(status => {
      status.textContent = value;
      status.hidden = !value;
    });
  }
  function setPaying(value) {
    state.kattamPaying = value;
    document.querySelectorAll('[data-pay]').forEach(control => { control.disabled = value; });
  }
  async function kattamHash(kind, inputs) {
    const pick = person => [person.birth_date, person.birth_time, Number(person.latitude), Number(person.longitude), person.timezone];
    const roles = kind === 'jathagam' ? ['person'] : ['bride', 'groom'];
    try {
      const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(`rightconnect-${kind}|${JSON.stringify(roles.map(role => pick(inputs[role])))}`));
      return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
    } catch (_) { return null; }
  }
  // Payment proofs (not birth details) are kept per tab so a paid report can be reopened or re-translated.
  function loadProofs() {
    try {
      const stored = JSON.parse(sessionStorage.getItem(PAID_KEY) || '{}');
      if (stored && typeof stored === 'object' && !Array.isArray(stored)) {
        for (const [hash, proof] of Object.entries(stored)) {
          if (/^[0-9a-f]{64}$/.test(hash) && proof && typeof proof.razorpay_payment_id === 'string') state.kattamProofs[hash] = proof;
        }
      }
    } catch (_) { return; }
  }
  function rememberProof(hash, proof) {
    if (!hash) return;
    state.kattamProofs[hash] = proof;
    const recent = Object.entries(state.kattamProofs).slice(-10);
    try { sessionStorage.setItem(PAID_KEY, JSON.stringify(Object.fromEntries(recent))); } catch (_) { return; }
  }
  const scripts = new Map();
  function loadScript(src) {
    if (!scripts.has(src)) scripts.set(src, new Promise((resolve, reject) => {
      const tag = document.createElement('script');
      tag.src = src;
      tag.async = true;
      tag.onload = resolve;
      tag.onerror = () => { scripts.delete(src); tag.remove(); reject(error('networkError')); };
      document.head.append(tag);
    }));
    return scripts.get(src);
  }
  async function startKattamPayment() {
    const kattam = state.kattam;
    if (!kattam || !kattam.report || !kattam.report.locked || state.kattamPaying || state.busy) return;
    setPaying(true);
    setPayStatus(t('payOpening'));
    try {
      await loadScript(RAZORPAY_CHECKOUT);
      if (!window.Razorpay) throw error('payUnavailable');
      const order = await porutham(`/${kattam.kind}/order`, kattamBody(kattam));
      if (!order || typeof order.order_id !== 'string' || typeof order.key_id !== 'string' || !Number.isInteger(order.amount)) throw error('invalidResponse');
      const email = state.session && state.session.user && state.session.user.email;
      const checkout = new window.Razorpay({
        key: order.key_id, order_id: order.order_id, amount: order.amount, currency: order.currency || 'INR',
        name: 'RightConnect', description: t(lockedKey('lockedTitle')), theme: { color: '#7d1410' },
        prefill: email ? { email } : {},
        handler: response => { confirmKattamPayment(kattam, response); },
        modal: { ondismiss: () => { if (state.kattamPaying && !state.kattamPending) { setPaying(false); setPayStatus(t('payCancelled')); } } }
      });
      checkout.on('payment.failed', () => setPayStatus(t('payFailed')));
      setPayStatus('');
      checkout.open();
    } catch (failure) {
      setPaying(false);
      setPayStatus(message(failure));
    }
  }
  async function confirmKattamPayment(kattam, response) {
    if (!response || typeof response.razorpay_payment_id !== 'string') return;
    const proof = { razorpay_order_id: response.razorpay_order_id, razorpay_payment_id: response.razorpay_payment_id, razorpay_signature: response.razorpay_signature };
    state.kattamPending = { kattam, response: proof };
    setPaying(true);
    setPayStatus(t('payVerifying'));
    let paid = false;
    try {
      const result = await porutham(`/${kattam.kind}/full`, { ...kattamBody(kattam), payment: proof });
      paid = Boolean(result && result.status === 'paid' && result.report);
      if (paid) {
        kattam.report = result.report;
        rememberProof(kattam.hash, proof);
      }
      state.kattamPayMessage = paid ? t('paidThanks') : t('payPending');
    } catch (failure) {
      state.kattamPayMessage = t('payVerifyError');
    }
    if (paid) state.kattamPending = null;
    state.kattamPaying = false;
    if (paid && state.session) loadAccount();
    if (state.kattam === kattam) {
      renderKattamReport();
      if (paid) {
        focusHeading('#report-heading');
        downloadKattamPdf();
      }
    }
  }
  const poruthamPage = () => document.body.dataset.servicePage === 'compatibility';
  async function loadAccount() {
    if (!poruthamPage()) return;
    if (!state.session) {
      state.account = null;
      renderSide();
      return;
    }
    const version = state.authVersion;
    try {
      const account = await porutham('/me', undefined, 'GET');
      if (version !== state.authVersion) return;
      state.account = account;
      if (account.pack) state.packOffer = account.pack;
    } catch (_) {
      if (version !== state.authVersion) return;
      state.account = null;
    }
    renderSide();
    if (state.kattam && state.kattam.report && state.kattam.report.locked && !$('#report-panel').hidden && !state.kattamPaying) renderKattamReport();
  }
  function shortDate(value) {
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? '' : new Intl.DateTimeFormat(state.language === 'ta' ? 'ta-IN' : 'en-GB', { dateStyle: 'medium' }).format(parsed);
  }
  function packBox() {
    const pack = state.packOffer;
    const box = text('div', undefined, 'side-pack');
    box.append(text('strong', t('packOffer').replace('{price}', rupees(pack.amount_paise)).replace('{n}', pack.reports).replace('{days}', pack.days)),
      text('small', t('packHelp')));
    const buy = button(t(state.session ? 'buyPack' : 'loginForPack'), buyPack, 'secondary', 'package');
    buy.dataset.pay = '';
    buy.disabled = state.kattamPaying || pack.available === false;
    box.append(buy);
    return box;
  }
  function renderSide() {
    const side = $('#porutham-side');
    if (!side) return;
    const account = state.account;
    const card = text('section', undefined, 'side-card');
    card.append(text('h2', t('accountTitle')));
    if (!state.session) {
      card.append(text('p', t('guestSide'), 'form-help'), button(t('login'), () => $('#login').click(), 'secondary', 'log-in'));
    } else if (!account) {
      card.append(text('p', t('accountError'), 'form-help'));
    } else if (account.admin) {
      card.append(text('p', t('adminBadge'), 'side-admin'));
    } else {
      card.append(text('p', account.credits
        ? `${t('creditsLeft').replace('{n}', account.credits)} · ${t('creditsUntil').replace('{date}', shortDate(account.pack_expires_at))}`
        : t('noCredits'), 'side-credits'));
    }
    if (!account || !account.admin) card.append(packBox());
    side.replaceChildren(card);
    if (state.session && account) side.append(historyCard(account));
    icons();
  }
  function historyCard(account) {
    const card = text('section', undefined, 'side-card side-history');
    card.append(text('h2', `${t('historyTitle')} (${account.history.length}/${account.history_limit})`),
      text('p', t('historyWarning').replace('{n}', account.history_limit), 'side-warning'));
    if (!account.history.length) {
      card.append(text('p', t('historyEmpty'), 'muted'));
      return card;
    }
    const list = text('ul', undefined, 'history-list');
    for (const entry of account.history) {
      const current = state.kattam && state.kattam.historyId === entry.id && !$('#report-panel').hidden;
      const row = text('li', undefined, `history-item${current ? ' is-current' : ''}`);
      const open = text('button', undefined, 'history-open');
      open.type = 'button';
      const jathagamEntry = entry.kind === 'jathagam';
      const label = jathagamEntry ? entry.bride : `${entry.groom} · ${entry.bride}`;
      const meta = text('span', undefined, 'history-meta');
      meta.append(text('span', t(`${jathagamEntry ? 'period' : 'level'}_${entry.level}`), `level-chip level-${entry.level}`),
        text('small', jathagamEntry ? t('historyJathagam') : `${entry.stars}/12 · ${entry.kattam}/4`));
      if (!entry.unlocked) {
        const lock = text('i');
        lock.dataset.lucide = 'lock';
        lock.setAttribute('aria-label', t('lockedEntry'));
        meta.append(lock);
      }
      open.append(text('span', label, 'history-names'), meta);
      open.addEventListener('click', () => openHistory(entry.id));
      const remove = text('button', undefined, 'history-delete');
      remove.type = 'button';
      remove.title = t('deleteHistory');
      remove.setAttribute('aria-label', `${t('deleteHistory')}: ${label}`);
      const bin = text('i');
      bin.dataset.lucide = 'trash-2';
      bin.setAttribute('aria-hidden', 'true');
      remove.append(bin);
      remove.addEventListener('click', () => removeHistory(entry));
      row.append(open, remove);
      list.append(row);
    }
    card.append(list);
    return card;
  }
  async function openHistory(id) {
    if (state.kattamPaying) return;
    await perform(async () => {
      const result = await porutham(`/history/${encodeURIComponent(id)}?language=${state.language}`, undefined, 'GET');
      const kind = result.kind === 'jathagam' ? 'jathagam' : 'kattam';
      const inputs = kind === 'jathagam' ? { person: result.inputs.person } : { bride: result.inputs.bride, groom: result.inputs.groom };
      applyOffer(result.unlock);
      state.kattam = { kind, inputs, selected: result.inputs.selected || null, hash: await kattamHash(kind, inputs), report: result.report, historyId: result.id };
      state.kattamPending = null;
      state.kattamPayMessage = '';
      state.selected = descriptorFor('compatibility');
      state.compatibilityStep = kind;
      state.kattamFrom = 'choose';
      state.inputs = inputs;
      renderKattamReport();
      renderSide();
      focusHeading('#report-heading');
    });
  }
  async function removeHistory(entry) {
    if (state.busy || !window.confirm(t('deleteHistoryConfirm'))) return;
    await perform(async () => {
      await porutham(`/history/${encodeURIComponent(entry.id)}`, undefined, 'DELETE');
      if (state.kattam && state.kattam.historyId === entry.id) state.kattam.historyId = null;
      await loadAccount();
    });
  }
  async function useCredit() {
    const kattam = state.kattam;
    if (!kattam || !kattam.report || !kattam.report.locked || state.kattamPaying || state.busy) return;
    setPaying(true);
    setPayStatus(t('loading'));
    try {
      const result = await porutham(`/${kattam.kind}/credit`, kattamBody(kattam));
      kattam.report = result.report;
      state.kattamPayMessage = '';
    } catch (failure) {
      state.kattamPayMessage = message(failure);
    }
    state.kattamPaying = false;
    if (state.kattam === kattam) renderKattamReport();
    await loadAccount();
  }
  async function buyPack() {
    if (!state.session) {
      $('#login').click();
      return;
    }
    if (state.kattamPaying || state.busy) return;
    setPaying(true);
    setPayStatus(t('payOpening'));
    try {
      await loadScript(RAZORPAY_CHECKOUT);
      if (!window.Razorpay) throw error('payUnavailable');
      const order = await porutham('/pack/order');
      if (!order || typeof order.order_id !== 'string' || typeof order.key_id !== 'string' || !Number.isInteger(order.amount)) throw error('invalidResponse');
      const checkout = new window.Razorpay({
        key: order.key_id, order_id: order.order_id, amount: order.amount, currency: order.currency || 'INR', name: 'RightConnect',
        description: t('packOffer').replace('{price}', rupees(order.amount)).replace('{n}', order.reports).replace('{days}', order.days),
        theme: { color: '#7d1410' }, prefill: state.session.user && state.session.user.email ? { email: state.session.user.email } : {},
        handler: response => { confirmPack(response); },
        modal: { ondismiss: () => { if (state.kattamPaying && !state.packConfirming) { setPaying(false); setPayStatus(t('payCancelled')); } } }
      });
      checkout.on('payment.failed', () => setPayStatus(t('payFailed')));
      setPayStatus('');
      checkout.open();
    } catch (failure) {
      setPaying(false);
      setPayStatus(message(failure));
      notice(message(failure));
    }
  }
  async function confirmPack(response) {
    state.packConfirming = true;
    setPayStatus(t('payVerifying'));
    let result = null;
    let outcome = t('payVerifyError');
    try {
      result = await porutham('/pack/verify', {
        razorpay_order_id: response.razorpay_order_id, razorpay_payment_id: response.razorpay_payment_id, razorpay_signature: response.razorpay_signature
      });
      outcome = result.status === 'paid' ? t('packBought').replace('{n}', result.credits) : t('payPending');
    } catch (_) { result = null; }
    state.packConfirming = false;
    setPaying(false);
    await loadAccount();
    setPayStatus(outcome);
    notice(outcome);
    if (result && result.status === 'paid' && state.kattam && state.kattam.report && state.kattam.report.locked && !$('#report-panel').hidden) await useCredit();
  }
  function pdfPages(holder, pageHeight) {
    const origin = holder.getBoundingClientRect().top;
    const total = Math.ceil(holder.scrollHeight);
    const blocks = Array.from(holder.querySelectorAll('h2, h3, h4, p, li, tr, figure, caption, summary, .match-verdict, .kattam-summary, .notice'), node => {
      const rect = node.getBoundingClientRect();
      return { top: rect.top - origin, bottom: rect.bottom - origin, heading: /^H[2-4]$/.test(node.tagName) };
    });
    const pages = [];
    for (let start = 0; total - start > 2;) {
      let end = Math.min(total, start + pageHeight);
      if (end < total) {
        const minimum = start + pageHeight * 0.4;
        end = blocks.filter(block => block.top < end && block.bottom > end && block.top >= minimum).reduce((cut, block) => Math.min(cut, block.top), end);
        const orphan = blocks.find(block => block.heading && block.top >= minimum && block.bottom <= end && end - block.bottom < 60);
        if (orphan) end = orphan.top;
      }
      pages.push({ start, end });
      start = end;
    }
    return pages;
  }
  async function downloadKattamPdf() {
    const kattam = state.kattam;
    if (!kattam || !kattam.report || kattam.report.locked || !kattam.node || state.pdfBusy) return;
    state.pdfBusy = true;
    document.querySelectorAll('[data-pdf]').forEach(control => { control.disabled = true; });
    setPayStatus(t('pdfPreparing'));
    const holder = text('div', undefined, 'kattam-pdf');
    holder.id = 'kattam-pdf';
    holder.lang = state.language;
    const head = text('header', undefined, 'kattam-pdf-head');
    head.append(text('strong', 'RightConnect', 'kattam-pdf-brand'), text('h2', kattam.report.title),
      text('p', kattam.report.subtitle),
      text('small', `${t('pdfGenerated')}: ${dateLabel(new Date().toISOString())}`));
    holder.append(head);
    if (kattam.placeNotes.length) {
      const box = text('div', undefined, 'notice');
      kattam.placeNotes.forEach(note => box.append(text('p', note)));
      holder.append(box);
    }
    holder.append(kattam.node.cloneNode(true));
    holder.querySelectorAll('details').forEach(details => { details.open = true; });
    document.body.append(holder);
    try {
      await Promise.all([loadScript(PDF_SCRIPTS[0]), loadScript(PDF_SCRIPTS[1])]);
      if (!window.html2canvas || !window.jspdf) throw error('pdfError');
      if (document.fonts && document.fonts.ready) await document.fonts.ready;
      const margin = 12;
      const contentWidth = 210 - margin * 2;
      const mmPerPx = contentWidth / holder.offsetWidth;
      const pages = pdfPages(holder, Math.floor((297 - margin - 16) / mmPerPx));
      // Render a few pages per canvas to stay under mobile canvas size limits.
      const chunks = [];
      for (const page of pages) {
        const last = chunks[chunks.length - 1];
        if (last && page.end - last.start <= 3200) { last.end = page.end; last.pages.push(page); }
        else chunks.push({ start: page.start, end: page.end, pages: [page] });
      }
      const pdf = new window.jspdf.jsPDF({ unit: 'mm', format: 'a4', compress: true });
      let pageNumber = 0;
      for (const chunk of chunks) {
        const canvas = await window.html2canvas(holder, {
          scale: 2, y: chunk.start, height: chunk.end - chunk.start, width: holder.offsetWidth,
          backgroundColor: '#ffffff', logging: false,
          onclone: clone => { const copy = clone.getElementById('kattam-pdf'); if (copy) copy.style.left = '0px'; }
        });
        const ratio = canvas.height / (chunk.end - chunk.start);
        for (const page of chunk.pages) {
          const slice = document.createElement('canvas');
          slice.width = canvas.width;
          slice.height = Math.max(1, Math.round((page.end - page.start) * ratio));
          const context = slice.getContext('2d');
          context.fillStyle = '#ffffff';
          context.fillRect(0, 0, slice.width, slice.height);
          context.drawImage(canvas, 0, Math.round((page.start - chunk.start) * ratio), canvas.width, slice.height, 0, 0, slice.width, slice.height);
          if (pageNumber) pdf.addPage();
          pdf.addImage(slice.toDataURL('image/jpeg', 0.9), 'JPEG', margin, margin, contentWidth, (page.end - page.start) * mmPerPx);
          pageNumber += 1;
        }
      }
      for (let index = 1; index <= pageNumber; index += 1) {
        pdf.setPage(index);
        pdf.setFontSize(8);
        pdf.setTextColor(125, 20, 16);
        pdf.text(`RightConnect  |  ${index} / ${pageNumber}`, 105, 290, { align: 'center' });
      }
      const url = URL.createObjectURL(pdf.output('blob'));
      const link = document.createElement('a');
      link.href = url;
      link.download = kattam.kind === 'jathagam' ? 'rightconnect-jathagam.pdf' : 'rightconnect-kattam-porutham.pdf';
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 60000);
      setPayStatus(t('pdfReady'));
    } catch (_) {
      setPayStatus(t('pdfError'));
    } finally {
      holder.remove();
      state.pdfBusy = false;
      document.querySelectorAll('[data-pdf]').forEach(control => { control.disabled = false; });
    }
  }
  async function changeReport(action, language, status) {
    const report = state.report;
    if (!report) return;
    await perform(async () => {
      const version = state.reportVersion;
      const result = await request(`/${encodeURIComponent(report.id)}/${action}`, { method: 'POST', token: state.capabilities.get(report.id), body: { language } });
      if (!validReport(result)) throw error('invalidResponse');
      if (version !== state.reportVersion) return;
      acceptReport(result);
    }, status, 'generating');
  }
  async function openReport(id) {
    const status = $('#report-panel .inline-status');
    await perform(async () => {
      const version = state.authVersion;
      const result = await request(`/${encodeURIComponent(id)}`, { token: state.capabilities.get(id) });
      if (version !== state.authVersion) return;
      if (!validReport(result)) throw error('invalidResponse');
      if (!state.report || state.report.id !== result.id) state.inputs = null;
      state.reportVersion += 1;
      setView('services');
      state.selected = descriptorFor(result.service_type) || null;
      acceptReport(result);
    }, status);
  }
  function renderRecovery() {
    const panel = $('#recovery-panel');
    panel.replaceChildren();
    panel.hidden = state.capabilities.size === 0;
    const heading = text('h2', t('recovery'));
    heading.id = 'recovery-title';
    panel.append(heading, text('p', t('recoveryHelp'), 'muted'));
    const list = text('ul', undefined, 'record-list');
    for (const id of Array.from(state.capabilities.keys()).reverse()) {
      const row = text('li', undefined, 'record-row');
      row.append(text('span', `${t('reportId')}: ${id}`));
      const open = button(t('open'), () => openReport(id), 'secondary', 'file-text');
      open.dataset.lock = '';
      row.append(open);
      list.append(row);
    }
    panel.append(list);
    icons();
  }
  function setView(view) {
    state.view = view;
    for (const key of ['services', 'history', 'family']) $(`#${key}-view`).hidden = key !== view;
    document.querySelectorAll('[data-view]').forEach(control => {
      if (control.dataset.view === view) control.setAttribute('aria-current', 'page');
      else control.removeAttribute('aria-current');
    });
  }
  async function showView(view) {
    if (state.busy || (view !== 'services' && !state.session)) return;
    if (state.view === 'services' && state.selected && !$('#input-panel').hidden) state.inputs = readInputs($('#input-panel form'), state.selected);
    captureFamilyDraft();
    notice('');
    setView(view);
    if (view === 'history') await loadHistory();
    if (view === 'family') await loadFamily();
  }
  async function loadHistory() {
    const container = $('#history-content');
    const status = text('p', t('loading'), 'inline-status');
    status.setAttribute('role', 'status');
    container.replaceChildren(status);
    const version = state.authVersion;
    await perform(async () => {
      const data = await request('/history/me', { authenticated: true });
      if (version !== state.authVersion) return;
      if (!Array.isArray(data.reports)) throw error('invalidResponse');
      const list = text('ul', undefined, 'record-list');
      for (const report of data.reports) {
        if (!validReport(report)) continue;
        const descriptor = descriptorFor(report.service_type);
        const row = text('li', undefined, 'record-row');
        const detail = text('div');
        detail.append(text('strong', descriptor ? titleFor(descriptor) : t('reportTitle')), text('small', `${t(report.status)} · ${dateLabel(report.created_at)}`));
        const open = button(t('open'), () => openReport(report.id), 'secondary', 'file-text');
        open.dataset.lock = '';
        row.append(detail, open);
        list.append(row);
      }
      container.replaceChildren(data.reports.length ? list : text('p', t('noHistory'), 'muted'));
    }, status);
    if (container.contains(status)) container.replaceChildren(button(t('reload'), loadHistory, 'secondary', 'refresh-cw'));
  }
  async function fetchMembers() {
    const version = state.authVersion;
    const data = await request('/family/members', { authenticated: true });
    if (version !== state.authVersion) return;
    if (!Array.isArray(data.members)) throw error('invalidResponse');
    state.members = data.members.filter(member => member && typeof member.id === 'string' && typeof member.label === 'string' && member.details);
    state.membersLoaded = true;
  }
  async function loadFamily() {
    const container = $('#family-content');
    const status = text('p', '', 'inline-status');
    status.setAttribute('role', 'status');
    container.replaceChildren(status);
    await perform(async () => {
      await fetchMembers();
      if (state.session) renderFamily();
    }, status);
    if (container.contains(status)) container.replaceChildren(button(t('reload'), loadFamily, 'secondary', 'refresh-cw'));
  }
  function renderFamily() {
    const container = $('#family-content');
    container.replaceChildren();
    if (!state.session) return;
    const add = button(t('addMember'), () => renderMemberEditor(), '', 'user-plus');
    const reload = button(t('reload'), loadFamily, 'secondary', 'refresh-cw');
    add.dataset.lock = '';
    reload.dataset.lock = '';
    const actions = text('div', undefined, 'row-actions');
    actions.append(add, reload);
    container.append(actions);
    const list = text('ul', undefined, 'record-list');
    if (!state.members.length) container.append(text('p', t('emptyFamily'), 'muted'));
    for (const member of state.members) {
      const row = text('li', undefined, 'record-row');
      row.append(text('strong', member.label));
      const actions = text('div', undefined, 'row-actions');
      const edit = button(t('editMember'), () => renderMemberEditor(member), 'secondary', 'pencil');
      const remove = button(t('deleteMember'), () => {
        if (state.busy || !window.confirm(t('deleteConfirm'))) return;
        perform(async () => {
          const version = state.authVersion;
          await request(`/family/members/${encodeURIComponent(member.id)}`, { method: 'DELETE', authenticated: true });
          if (version !== state.authVersion) return;
          state.members = state.members.filter(item => item.id !== member.id);
          refreshSavedPickers();
          state.familyEditor = null;
          renderFamily();
          notice(t('deleted'));
        });
      }, 'danger', 'trash-2');
      edit.dataset.lock = '';
      remove.dataset.lock = '';
      actions.append(edit, remove);
      row.append(actions);
      list.append(row);
    }
    container.append(list);
    if (state.familyEditor) renderMemberEditor(state.familyEditor.member, state.familyEditor.draft);
    icons();
  }
  function renderMemberEditor(member = null, draft = null) {
    if (state.busy && !state.familyEditor) return;
    $('#family-content .family-editor')?.remove();
    state.familyEditor = { member, draft };
    const form = text('form', undefined, 'family-editor');
    form.noValidate = true;
    const heading = text('h3', t(member ? 'editMember' : 'addMember'));
    heading.id = 'member-editor-heading';
    form.append(heading);
    const editable = document.createElement('fieldset');
    editable.dataset.lock = '';
    makeField(editable, { name: 'member-label', label: 'memberLabel', value: draft ? draft.label : member ? member.label : '', maxLength: 100 });
    birthGroup(editable, 'family', 'birth', draft ? draft.details : member ? member.details : {}, false);
    check(editable, 'save-consent', 'saveConsent');
    const actions = text('div', undefined, 'form-actions');
    const save = text('button', t(member ? 'updateMember' : 'saveMember'), 'button');
    save.type = 'submit';
    const cancel = button(t('cancel'), () => { state.familyEditor = null; form.remove(); }, 'quiet', 'x');
    actions.append(save, cancel);
    editable.append(actions);
    const status = text('p', '', 'inline-status');
    status.hidden = true;
    status.setAttribute('role', 'status');
    form.append(editable, status);
    form.addEventListener('submit', event => {
      event.preventDefault();
      if (state.busy || !validateForm(form)) return;
      const payload = { label: form.elements.namedItem('member-label').value.trim(), details: getBirth(form, 'family'), consent: true };
      if (!payload.label) { form.elements.namedItem('member-label').focus(); return; }
      perform(async () => {
        const version = state.authVersion;
        await request(`/family/members${member ? `/${encodeURIComponent(member.id)}` : ''}`, { method: member ? 'PUT' : 'POST', body: payload, authenticated: true });
        if (version !== state.authVersion) return;
        state.familyEditor = null;
        renderFamily();
        notice(t('saved'));
        try {
          await fetchMembers();
          if (version !== state.authVersion) return;
          refreshSavedPickers();
          renderFamily();
        } catch (_) { notice(`${t('saved')} ${t('familyError')}`); }
      }, status);
    });
    $('#family-content').append(form);
    icons();
  }
  function refreshSavedPickers() {
    document.querySelectorAll('#input-panel select[name$="-member"]').forEach(picker => {
      const selected = picker.value;
      picker.replaceChildren();
      for (const [value, label] of [['', t('manualMember')], ...state.members.map(member => [member.id, member.label])]) {
        const option = text('option', label);
        option.value = value;
        picker.append(option);
      }
      picker.value = state.members.some(member => member.id === selected) ? selected : '';
    });
  }
  function captureFamilyDraft() {
    const editor = $('#family-content .family-editor');
    if (editor && state.familyEditor) state.familyEditor.draft = { label: editor.elements.namedItem('member-label').value, details: getBirth(editor, 'family') };
  }
  async function applySession(session) {
    const previousId = state.session && state.session.user.id;
    const nextId = session && session.user.id;
    state.session = session;
    $('#login').hidden = Boolean(session);
    $('#logout').hidden = !session;
    document.querySelectorAll('[data-auth]').forEach(element => { element.hidden = !session; });
    updateLanguageText();
    if (previousId === nextId) return;
    state.authVersion += 1;
    state.reportVersion += 1;
    state.members = [];
    state.membersLoaded = false;
    state.familyEditor = null;
    $('#family-content').replaceChildren();
    $('#history-content').replaceChildren();
    if (poruthamPage()) {
      if (previousId) {
        state.kattam = null;
        state.kattamPending = null;
        state.kattamPayMessage = '';
        state.quickMatch = null;
        selectService(descriptorFor('compatibility'));
      }
      await loadAccount();
      return;
    }
    if (previousId) {
      state.inputs = null;
      state.selected = null;
      $('#input-panel').replaceChildren();
      $('#input-panel').hidden = true;
      if (state.report && !state.capabilities.has(state.report.id)) {
        state.report = null;
        $('#report-panel').replaceChildren();
        $('#report-panel').hidden = true;
        $('#catalogue').hidden = false;
      }
      if (!state.report) $('#catalogue').hidden = false;
      setView('services');
    }
    if (state.selected && !$('#input-panel').hidden && !state.busy) {
      captureSelectedInputs();
      rerenderSelectedInput();
    }
    if (session) {
      try { await fetchMembers(); refreshSavedPickers(); }
      catch (failure) {
        if (state.session) {
          notice(t(failure.key === 'onboardingError' ? 'onboardingError' : 'familyError'));
          if (failure.key === 'onboardingError') {
            const registration = text('a', t('completeAccount'), 'registration-link');
            registration.href = '/pages/auth.html';
            $('#global-status').append(' ', registration);
          }
        }
      }
    }
  }
  async function initAuth() {
    try {
      const response = await fetch('/api/v1/auth/provider-config', { cache: 'no-store' });
      if (!response.ok) throw error('loginUnavailable');
      const config = await response.json();
      if (!config.supabase_url || !config.supabase_publishable_key || !window.supabase) throw error('loginUnavailable');
      state.client = window.supabase.createClient(config.supabase_url, config.supabase_publishable_key);
      const { data, error: sessionError } = await state.client.auth.getSession();
      if (sessionError) throw error('loginUnavailable');
      await applySession(data.session);
      state.client.auth.onAuthStateChange((_event, session) => {
        setTimeout(() => { applySession(session).catch(() => notice(t('authError'))); }, 0);
      });
      $('#login').disabled = false;
    } catch (_) { state.client = null; $('#login').disabled = true; }
  }
  async function switchLanguage(next) {
    if (state.busy || next === state.language) return;
    if (state.selected && !$('#input-panel').hidden) captureSelectedInputs();
    captureFamilyDraft();
    state.language = next;
    notice('');
    updateLanguageText();
    renderCatalogue();
    renderRecovery();
    renderSide();
    if (state.selected && !$('#input-panel').hidden) {
      if (state.selected.key === 'compatibility' && state.compatibilityStep === 'rasi' && state.quickMatch) {
        await perform(async () => {
          state.quickMatch = await porutham('/rasi', { language: next, ...state.quickInputs });
          renderQuickMatchResults();
        });
      } else rerenderSelectedInput();
    }
    if (state.view === 'family') renderFamily();
    if (state.view === 'history') await loadHistory();
    if (state.kattam && state.kattam.report && !$('#report-panel').hidden && !state.report) {
      await perform(async () => {
        await loadKattam(state.kattam);
        renderKattamReport();
      });
    }
    if (state.report) {
      renderReport();
      if (state.report.status === 'completed' && state.report.language !== next) await changeReport('language', next, $('#report-panel .inline-status'));
    }
  }
  $('#language').addEventListener('change', event => { switchLanguage(event.target.value); });
  $('#reload-services').addEventListener('click', () => perform(loadServices));
  document.querySelectorAll('[data-view]').forEach(control => control.addEventListener('click', () => showView(control.dataset.view)));
  $('#login').addEventListener('click', () => perform(async () => {
    if (!state.client) throw error('loginUnavailable');
    const { error: oauthError } = await state.client.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: `${location.origin}${location.pathname}` } });
    if (oauthError) throw error('loginFailed');
  }));
  $('#logout').addEventListener('click', () => perform(async () => {
    const { error: signOutError } = await state.client.auth.signOut();
    if (signOutError) throw error('authError');
    await applySession(null);
  }));
  window.addEventListener('beforeprint', () => {
    document.querySelectorAll('details.kattam-expert').forEach(details => { details.open = true; });
  });
  loadCapabilities();
  loadProofs();
  updateLanguageText();
  renderRecovery();
  if (document.body.dataset.servicePage === 'compatibility') {
    selectService(descriptorFor('compatibility'));
    if (new URLSearchParams(location.search).get('service') === 'jathagam') openReportForm('jathagam');
    renderSide();
  } else loadServices();
  initAuth();
})();