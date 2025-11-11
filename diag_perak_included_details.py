import os
from services.calendarific_service import fetch_calendarific_holidays


def reason_for_inclusion(loc_str: str, state: str = 'Perak'):
    s = (loc_str or '').strip()
    s_lower = s.lower()
    if s_lower in ('', 'all', 'all malaysia', 'nationwide'):
        return 'all/blank', []
    if 'all except' in s_lower:
        after = s_lower.split('all except', 1)[1]
        toks = [t.strip().strip('.') for t in after.replace('&', ',').split(',') if t.strip()]
        # if state token present in exception list -> excluded; else included
        st = state.strip().lower()
        # naive check for perak tokens
        perak_aliases = ['perak', 'prk']
        for a in perak_aliases:
            if a in toks or a in ' '.join(toks):
                return 'all-except (perak excluded)', toks
        return 'all-except (included)', toks

    # otherwise check for perak tokens in loc_str
    loc_parts = [p.strip().strip('.') for p in s_lower.replace('&', ',').replace(' and ', ',').split(',') if p.strip()]
    toks = loc_parts
    for a in ['perak', 'prk']:
        if a in toks or a in ' '.join(toks):
            return 'token-match', toks

    # fallback: not matched
    return 'no-match', toks


def run(year=2025, country='MY', state='Perak'):
    api_key = os.environ.get('CALENDARIFIC_API_KEY')
    if not api_key:
        print('ERROR: Set CALENDARIFIC_API_KEY in environment to run diagnostic')
        return

    # Exclude national/all holidays so we can surface state-specific inclusions
    # Also exclude astronomical/observance entries for this diagnostic
    filtered = fetch_calendarific_holidays(year, country=country, state=state, include_national=False, include_observances=False)
    print(f'Perak-filtered returned {len(filtered)} entries')
    print('\nDetailed inclusion reasons:')
    for d, name, loc in filtered:
        reason, toks = reason_for_inclusion(loc, state=state)
        print(f'  {d} - {name} - locations="{loc}" -> {reason}; tokens={toks}')


if __name__ == '__main__':
    run()
