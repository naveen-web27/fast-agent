(() => {
  'use strict';

  const API = '/api/v1/ai-reports';
  const CAPABILITY_KEY = 'rightconnect-ai-report-capabilities-v1';
  const words = {
    ta: {
      appTitle: 'தமிழ் ஜோதிடம் & கலைகள் AI அறிக்கைகள்', eyebrow: 'பாரம்பரியக் கலைகள்',
      compatibilityPageTitle: 'திருமணப் பொருத்தம்', compatibilityNav: 'திருமணப் பொருத்தம்',
      compatibilityDisclaimer: 'பன்னிரண்டு பாரம்பரிய விதிகள் ஒப்பிடப்படுகின்றன. இவை அறிவியல் கணிப்போ திருமண வெற்றியின் சதவீதமோ அல்ல. வர்ணம் ஒரு வரலாற்று, சாதி சார்ந்த வகைப்பாடு; இது யாருடைய மதிப்பையும் தீர்மானிக்காது.',
      skip: 'உள்ளடக்கத்திற்குச் செல்ல', language: 'மொழி', views: 'பகுதிகள்', services: 'சேவைகள்',
      chooseService: 'சேவையைத் தேர்ந்தெடுக்கவும்', loadingServices: 'சேவைகள் ஏற்றப்படுகின்றன…',
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
      name: 'பெயர்', birthDate: 'பிறந்த தேதி', birthTime: 'பிறந்த நேரம்', localTime: 'பிறந்த இடத்தின் உள்ளூர் நேரம்; நேரம் தெரியாவிட்டால் ஊகிக்க வேண்டாம்.',
      cityPreset: 'நகரத் தேர்வு', manualCity: 'வேறு இடம் / கைமுறை', place: 'பிறந்த இடம்', latitude: 'அட்சரேகை', longitude: 'தீர்க்கரேகை', timezone: 'IANA நேர மண்டலம்',
      locationHelp: 'நகர மைய ஆயத்தொலைவுகள் மட்டுமே. பிறந்த இடத்திற்கேற்ப திருத்தவும். மற்ற இடங்களுக்கு சரியான ஆயத்தொலைவுகளை நீங்களே உள்ளிடவும்; தானியங்கி இடத்தேடல் இல்லை.',
      confirmLocation: 'பிறந்த இடம், அட்சரேகை, தீர்க்கரேகை மற்றும் நேர மண்டலத்தைச் சரிபார்த்து உறுதிப்படுத்துகிறேன்.',
      timezoneHelp: 'எ.கா. Asia/Kolkata. பிறந்த தேதிக்கான உள்ளூர் நேர மண்டலத்தை உறுதிப்படுத்தவும்.',
      savedMember: 'சேமித்த குடும்ப உறுப்பினர்', manualMember: 'புதிய விவரங்களை உள்ளிடு',
      fullName: 'முழுப் பெயர் (ஆங்கில எழுத்துகளில்)', englishNameHelp: 'எண் கணிதத்திற்கு வழக்கமாகப் பயன்படுத்தும் ஆங்கிலப் பெயர் எழுத்துக்கூட்டலை உள்ளிடவும்.',
      englishNameError: 'பெயரை ஆங்கில எழுத்துகளில் உள்ளிடவும்.', invalidTimezone: 'சரியான IANA நேர மண்டலத்தை உள்ளிடவும்.',
      facing: 'வீடு எதிர்நோக்கும் திசை', main_door: 'முதன்மை வாசல் திசை', kitchen: 'சமையலறை அமைந்த திசை', bedroom: 'படுக்கையறை அமைந்த திசை',
      directionHelp: 'வீட்டின் மையத்திலிருந்து அறைகள் அமைந்த திசையைத் தேர்ந்தெடுக்கவும்.',
      N: 'வடக்கு', NE: 'வடகிழக்கு', E: 'கிழக்கு', SE: 'தென்கிழக்கு', S: 'தெற்கு', SW: 'தென்மேற்கு', W: 'மேற்கு', NW: 'வடமேற்கு',
      gender: 'பெயர் வகை', neutral: 'பாலினச் சார்பற்றது', male: 'ஆண்', female: 'பெண்', rasi: 'ராசி', period: 'காலம்', daily: 'தினசரி', weekly: 'வாராந்திர',
      reportConsent: 'இந்த அறிக்கைக்காக விவரங்களைத் தற்காலிகமாகச் சேமித்து, AI சேவை வழங்குநருக்கு அனுப்ப அனுமதிக்கிறேன். மற்றவரின் விவரங்களைப் பகிர அவரின் அனுமதி உள்ளது. குடும்பப் பட்டியலில் தானாகச் சேமிக்கப்படாது.',
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
      appTitle: 'Tamil Astrology & Arts AI Reports', eyebrow: 'Traditional arts', skip: 'Skip to content', language: 'Language', views: 'Views', services: 'Services',
      compatibilityPageTitle: 'Marriage Compatibility', compatibilityNav: 'Marriage compatibility',
      compatibilityDisclaimer: 'This compares twelve traditional rules. They are not scientific predictions or a marriage-success percentage. Varna is a historical caste-coded classification; it does not determine anyone’s worth.',
      chooseService: 'Choose a service', loadingServices: 'Loading services…', login: 'Sign in with Google', logout: 'Sign out', guest: 'Guest', signedIn: 'Signed in',
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
      birth: 'Birth details', bride: 'Bride’s birth details', groom: 'Groom’s birth details', name: 'Name', birthDate: 'Birth date', birthTime: 'Birth time',
      localTime: 'Local time at the birthplace. Do not guess an unknown birth time.', cityPreset: 'City preset', manualCity: 'Other place / manual',
      place: 'Birthplace', latitude: 'Latitude', longitude: 'Longitude', timezone: 'IANA timezone',
      locationHelp: 'Presets are city-centre coordinates. Adjust to the actual birthplace. Enter accurate coordinates for other places; there is no automatic geocoding.',
      confirmLocation: 'I have checked and confirm the birthplace, latitude, longitude and timezone.', timezoneHelp: 'For example, Asia/Kolkata. Confirm the local timezone for the birth date.',
      savedMember: 'Saved family member', manualMember: 'Enter new details', fullName: 'Full name (English spelling)', englishNameHelp: 'Use the English spelling of the name normally used for numerology.',
      englishNameError: 'Enter the name in English letters.', invalidTimezone: 'Enter a valid IANA timezone.',
      facing: 'House facing direction', main_door: 'Main door direction', kitchen: 'Kitchen location', bedroom: 'Bedroom location', directionHelp: 'Choose room directions relative to the centre of the house.',
      N: 'North', NE: 'Northeast', E: 'East', SE: 'Southeast', S: 'South', SW: 'Southwest', W: 'West', NW: 'Northwest',
      gender: 'Name category', neutral: 'Gender neutral', male: 'Male', female: 'Female', rasi: 'Rasi', period: 'Period', daily: 'Daily', weekly: 'Weekly',
      reportConsent: 'I consent to temporary report storage and sending these details to the AI provider. I have permission to share anyone else’s details. They will not be automatically saved to my family list.',
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
    { key: 'horoscope', page: 'jathaka-palan.html', icon: 'orbit', ta: ['ஜாதகம்', 'பிறந்த நேரம் மற்றும் இடத்தின் அடிப்படையில் பாரம்பரிய ஜாதக விளக்கம்.'], en: ['Horoscope', 'A traditional interpretation based on birth time and place.'] },
    { key: 'compatibility', page: 'thirumana-porutham.html', icon: 'heart-handshake', ta: ['திருமணப் பொருத்தம்', 'பன்னிரண்டு பாரம்பரியப் பொருத்தங்களை ஒப்பிடும் தனிப்பட்ட அறிக்கை.'], en: ['Compatibility', 'A dedicated report comparing twelve traditional checks.'] },
    { key: 'numerology', page: 'numerology.html', icon: 'binary', ta: ['எண் கணிதம்', 'ஆங்கிலப் பெயர் மற்றும் பிறந்த தேதியின் எண் கணித விளக்கம்.'], en: ['Numerology', 'Traditional number interpretations of an English name and birth date.'] },
    { key: 'vastu', page: 'vastu.html', icon: 'house', ta: ['வாஸ்து', 'வீடு மற்றும் அறைகளின் திசைகள் பற்றிய பாரம்பரியக் கருத்துகள்.'], en: ['Vastu', 'Traditional perspectives on home and room directions.'] },
    { key: 'gemstone', page: 'gemstone.html', icon: 'gem', ta: ['ரத்தினக் கற்கள்', 'பிறந்த விவரங்களின் அடிப்படையில் பாரம்பரிய ரத்தின விளக்கம்.'], en: ['Gemstones', 'Traditional gemstone interpretations using birth details.'] },
    { key: 'baby-names', page: 'baby-names.html', icon: 'baby', ta: ['குழந்தைப் பெயர்கள்', 'பிறந்த விவரங்களுடன் குழந்தைப் பெயர் பரிந்துரைகள்.'], en: ['Baby names', 'Name suggestions using birth details and a name category.'] },
    { key: 'forecast', page: 'rasi-forecast.html', icon: 'sun', ta: ['ராசி பலன்', 'தேர்ந்தெடுத்த ராசிக்கான தினசரி அல்லது வாராந்திர பாரம்பரியப் பலன்.'], en: ['Rasi forecast', 'Daily or weekly traditional readings for your selected rasi.'] }
  ];
  const cities = [
    ['Chennai', 'சென்னை', 13.0827, 80.2707, 'Asia/Kolkata'],
    ['Madurai', 'மதுரை', 9.9252, 78.1198, 'Asia/Kolkata'],
    ['Coimbatore', 'கோயம்புத்தூர்', 11.0168, 76.9558, 'Asia/Kolkata'],
    ['Trichy', 'திருச்சி', 10.7905, 78.7047, 'Asia/Kolkata'],
    ['Jaffna', 'யாழ்ப்பாணம்', 9.6615, 80.0255, 'Asia/Colombo'],
    ['Singapore', 'சிங்கப்பூர்', 1.3521, 103.8198, 'Asia/Singapore'],
    ['London', 'லண்டன்', 51.5074, -0.1278, 'Europe/London']
  ];
  const rasis = {
    ta: ['மேஷம்', 'ரிஷபம்', 'மிதுனம்', 'கடகம்', 'சிம்மம்', 'கன்னி', 'துலாம்', 'விருச்சிகம்', 'தனுசு', 'மகரம்', 'கும்பம்', 'மீனம்'],
    en: ['Mesha (Aries)', 'Rishabha (Taurus)', 'Mithuna (Gemini)', 'Kataka (Cancer)', 'Simha (Leo)', 'Kanya (Virgo)', 'Tula (Libra)', 'Vrischika (Scorpio)', 'Dhanus (Sagittarius)', 'Makara (Capricorn)', 'Kumbha (Aquarius)', 'Meena (Pisces)']
  };
  const state = {
    language: 'ta', services: [], aiAvailable: false, selected: null, session: null,
    client: null, members: [], membersLoaded: false, report: null, inputs: null,
    busy: false, view: 'services', familyEditor: null, capabilities: new Map(),
    authVersion: 0, reportVersion: 0, storageWarning: false, catalogueError: null
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
    document.title = `${t(document.body.dataset.servicePage === 'compatibility' ? 'compatibilityPageTitle' : 'appTitle')} | RightConnect`;
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
    catalogueStatus.textContent = state.catalogueError ? message(state.catalogueError) : state.aiAvailable ? '' : t('aiUnavailable');
    catalogueStatus.hidden = !catalogueStatus.textContent;
    $('#reload-services').hidden = state.aiAvailable && !state.catalogueError;
    for (const [index, descriptor] of descriptors.entries()) {
      const service = state.services.find(item => item.key === descriptor.key);
      const available = Boolean(state.aiAvailable && service && service.available === true);
      const card = text('a', undefined, 'service-card');
      card.href = `/pages/${descriptor.page}`;
      const symbol = text('span', undefined, 'service-icon');
      symbol.setAttribute('aria-hidden', 'true');
      const icon = text('i');
      icon.dataset.lucide = descriptor.icon;
      symbol.append(icon, text('span', String(index + 1).padStart(2, '0'), 'icon-fallback'));
      card.append(symbol, text('span', titleFor(descriptor), 'service-title'));
      card.append(text('span', service && service[`description_${state.language}`] || descriptor[state.language][1], 'service-description'));
      if (!available) {
        const reasons = service && Array.isArray(service.unavailable_reasons) ? service.unavailable_reasons : [];
        const labels = { feature_disabled: 'featureDisabled', ai_provider_missing: 'providerMissing', rate_limit_secret_missing: 'rateSaltMissing', ephemeris_missing: 'ephemerisMissing' };
        if (descriptor.key === 'compatibility' && reasons.length) {
          card.append(text('span', reasons.map(reason => t(labels[reason] || 'unavailable')).join(' '), 'unavailable'));
        } else {
          card.append(text('span', descriptor.key === 'compatibility' ? t('unavailable') : t('comingSoon'), 'unavailable'));
        }
      }
      grid.append(card);
    }
    $('#compatibility-only-note')?.remove();
    if (!document.body.dataset.servicePage) {
      const guidance = text('p', t('compatibilityOnly'), 'form-help');
      guidance.id = 'compatibility-only-note';
      grid.after(guidance);
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
    const group = document.createElement('fieldset');
    group.dataset.birth = prefix;
    group.append(text('legend', t(heading)));
    const controls = {};
    if (state.session && allowSaved) {
      const pickerWrap = text('div', undefined, 'saved-picker');
      const picker = makeField(pickerWrap, {
        name: `${prefix}-member`, label: 'savedMember', required: false,
        options: [['', t('manualMember')], ...state.members.map(member => [member.id, member.label])]
      });
      group.append(pickerWrap);
      picker.addEventListener('change', () => {
        const member = state.members.find(item => item.id === picker.value);
        for (const [key, control] of Object.entries(controls)) control.value = member && member.details[key] !== undefined ? member.details[key] : key === 'timezone' ? 'Asia/Kolkata' : '';
        preset.value = '';
        confirmation.checked = false;
      });
    }
    const grid = text('div', undefined, 'field-grid');
    const definitions = [
      ['name', 'name', 'text', { required: false, maxLength: 100 }],
      ['birth_date', 'birthDate', 'date', { min: '1900-01-01', max: today() }],
      ['birth_time', 'birthTime', 'time', { help: 'localTime', step: 1 }]
    ];
    for (const [key, label, type, extras] of definitions) controls[key] = makeField(grid, { name: `${prefix}.${key}`, label, type, value: details[key] || '', ...extras });
    const preset = makeField(grid, { name: `${prefix}-city`, label: 'cityPreset', required: false, options: [['', t('manualCity')], ...cities.map(city => [city[0], state.language === 'ta' ? city[1] : city[0]])] });
    controls.place = makeField(grid, { name: `${prefix}.place`, label: 'place', value: details.place || '', maxLength: 160 });
    controls.place.minLength = 2;
    controls.latitude = makeField(grid, { name: `${prefix}.latitude`, label: 'latitude', type: 'number', min: -90, max: 90, step: 'any', value: details.latitude === undefined ? '' : details.latitude });
    controls.longitude = makeField(grid, { name: `${prefix}.longitude`, label: 'longitude', type: 'number', min: -180, max: 180, step: 'any', value: details.longitude === undefined ? '' : details.longitude });
    controls.timezone = makeField(grid, { name: `${prefix}.timezone`, label: 'timezone', value: details.timezone || 'Asia/Kolkata', maxLength: 80, help: 'timezoneHelp' });
    group.append(grid, text('p', t('locationHelp'), 'form-help'));
    const confirmation = check(group, `${prefix}-confirmed`, 'confirmLocation');
    for (const key of ['place', 'latitude', 'longitude', 'timezone']) controls[key].addEventListener('input', () => { confirmation.checked = false; preset.value = ''; });
    preset.addEventListener('change', () => {
      const city = cities.find(item => item[0] === preset.value);
      if (city) {
        controls.place.value = state.language === 'ta' ? city[1] : city[0];
        controls.latitude.value = city[2];
        controls.longitude.value = city[3];
        controls.timezone.value = city[4];
      } else {
        controls.place.value = '';
        controls.latitude.value = '';
        controls.longitude.value = '';
        controls.timezone.value = 'Asia/Kolkata';
      }
      confirmation.checked = false;
    });
    parent.append(group);
  }
  function getBirth(form, prefix) {
    const value = key => form.elements.namedItem(`${prefix}.${key}`).value.trim();
    const coordinate = key => value(key) === '' ? '' : Number(value(key));
    return { name: value('name'), birth_date: value('birth_date'), birth_time: value('birth_time'), place: value('place'), latitude: coordinate('latitude'), longitude: coordinate('longitude'), timezone: value('timezone') };
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
    if (descriptor.key === 'compatibility') return { bride: getBirth(form, 'bride'), groom: getBirth(form, 'groom') };
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
    state.reportVersion += 1;
    notice('');
    $('#report-panel').hidden = true;
    $('#catalogue').hidden = true;
    renderInput(inputs);
    focusHeading('#form-title');
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
    const heading = text('h2', titleFor(descriptor));
    heading.id = 'form-title';
    top.append(heading, button(t('back'), showCatalogue, 'quiet', 'arrow-left'));
    panel.append(top);
    const form = document.createElement('form');
    form.noValidate = true;
    const editable = document.createElement('fieldset');
    editable.dataset.lock = '';
    if (descriptor.key === 'compatibility') {
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
    check(editable, 'report-consent', 'reportConsent');
    const submit = text('button', t('generate'), 'button');
    submit.type = 'submit';
    submit.dataset.lock = '';
    const actions = text('div', undefined, 'form-actions');
    actions.append(submit);
    editable.append(actions);
    const status = text('p', '', 'inline-status');
    status.setAttribute('role', 'status');
    status.hidden = true;
    form.append(editable, status);
    form.addEventListener('submit', event => {
      event.preventDefault();
      if (state.busy || !validateForm(form)) return;
      const inputs = readInputs(form, descriptor);
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
      const draft = readInputs($('#input-panel form'), state.selected);
      renderInput(draft);
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
    if (state.selected && !$('#input-panel').hidden) state.inputs = readInputs($('#input-panel form'), state.selected);
    captureFamilyDraft();
    state.language = next;
    notice('');
    updateLanguageText();
    renderCatalogue();
    renderRecovery();
    if (state.selected && !$('#input-panel').hidden) renderInput(state.inputs || {});
    if (state.view === 'family') renderFamily();
    if (state.view === 'history') await loadHistory();
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
    const { error: oauthError } = await state.client.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: `${location.origin}/pages/services.html` } });
    if (oauthError) throw error('loginFailed');
  }));
  $('#logout').addEventListener('click', () => perform(async () => {
    const { error: signOutError } = await state.client.auth.signOut();
    if (signOutError) throw error('authError');
    await applySession(null);
  }));
  // TODO: Add payment integration only when a checkout contract is available.
  // TODO: Add an explicit print-to-PDF action after print output is verified.
  loadCapabilities();
  updateLanguageText();
  renderRecovery();
  loadServices();
  initAuth();
})();