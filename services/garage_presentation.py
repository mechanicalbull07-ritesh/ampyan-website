"""Display metadata only; membership, status and timing come from the API."""
import json
from pathlib import Path
LABELS = json.loads(Path(__file__).with_name('checklist_labels.json').read_text())
def checklist_rows(checklist):
    rows = []
    for item in checklist.get('items', []):
        copy = dict(item)
        copy.update(LABELS.get(item.get('component'), {
            'title': item.get('label') or 'Vehicle inspection',
            'guidance': 'Have a qualified workshop review this item.', 'group': 'Vehicle'}))
        copy['timing'] = ('Do now' if item.get('status') in ('DO NOW', 'Critical', 'Overdue') else
            'At next service' if checklist.get('mode') != 'VERIFIED_OEM_SCHEDULE' else item.get('status', 'Monitor'))
        rows.append(copy)
    return rows
