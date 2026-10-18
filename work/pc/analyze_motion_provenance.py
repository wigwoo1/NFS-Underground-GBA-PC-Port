"""Association evidence only. No variant is automatically approved for rendering."""
from pathlib import Path
import json,hashlib,collections
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace\NFSUG-pc-motion-provenance-tests');path=base/'provenance-audit-report.json';audit=json.loads(path.read_text());owners={tuple(row['owner']):row for row in audit['owners_data']}
variants={'source_identity':(), 'source_and_region_owner':(1,), 'source_and_region_pass':(2,), 'source_and_mask':(3,), 'source_and_object':(4,), 'source_owner_pass':(1,2), 'source_pass_mask':(2,3), 'source_owner_pass_object':(1,2,4), 'source_full_ownership':(1,2,3,4), 'source_region_table_id':(13,), 'source_region_pass_table_id':(2,13)}
rows=[]
for label,fields in variants.items():
 def key(draw):return tuple(draw['identity']),tuple(draw['pass_identity']),tuple((draw['original_command_words'][i]&65535) if i==13 else draw['original_command_words'][i] for i in fields)
 duplicates=0;totals=dict(unique_shared=0,ambiguous_old=0,old_only=0,new_only=0)
 for owner in owners.values():duplicates+=sum(n for n in collections.Counter(key(d) for d in owner['draws'] if d['type']==3).values() if n>1)
 for pair in audit['pair_data']:
  a=collections.Counter(key(d) for d in owners[tuple(pair['older'])]['draws'] if d['type']==3);b=collections.Counter(key(d) for d in owners[tuple(pair['newer'])]['draws'] if d['type']==3)
  totals['unique_shared']+=sum(n==1 and b[x]==1 for x,n in a.items());totals['ambiguous_old']+=sum(n for x,n in a.items() if n>1 or b[x]>1);totals['old_only']+=sum(n for x,n in a.items() if not b[x]);totals['new_only']+=sum(n for x,n in b.items() if not a[x])
 rows.append(dict(variant=label,command_word_indices=fields,duplicate_rows=duplicates,**totals))
report=dict(result='ORIGINAL_COMMAND_ASSOCIATION_VARIANT_EVIDENCE',complete_owner_coverage=audit['complete_owner_coverage'],available_owners=audit['owners'],missing_owners=audit['failed_owners'],pairs=audit['pairs'],variants=rows,audit_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),approved_for_live_association=False,limit='Counts on available captured owners only. Region owner is an executor occurrence; visibility mask/record and model identities may vary. Semantic stability and 24 missing owners still require proof.')
(base/'provenance-association-analysis.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
