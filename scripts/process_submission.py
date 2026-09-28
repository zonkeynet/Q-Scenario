"""Trusted default-branch worker. Treat issue body strictly as JSON data, never as code."""
import hashlib
import json
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from catalog import load, validate, encoded, build_index, package_path, require

def extract(body):
    require(type(body) is str and len(body.encode('utf-8'))<=60000,'Issue size')
    prefix='Q-P1NG marketplace submission. Manual maintainer review required.\n\n```json\n'
    require(body.startswith(prefix) and body.endswith('\n```\n'),'Submission envelope')
    return validate(load(body[len(prefix):-5].encode('utf-8')))

def main():
    event=load(Path(os.environ['GITHUB_EVENT_PATH']).read_bytes())
    # Label must be applied by a repository collaborator; outsiders cannot trigger privileged publication.
    if event.get('action')!='labeled' or event.get('label',{}).get('name')!='marketplace-submission':
        return
    issue=event.get('issue',{})
    require(not issue.get('pull_request') and type(issue.get('number')) is int and issue['number']>0,'Issue number')
    package=extract(issue.get('body',''))
    repository=os.environ['GITHUB_REPOSITORY']
    require(re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repository),'Repository')
    token=os.environ['GITHUB_TOKEN']
    def api(path, data=None, missing_ok=False):
        req=urllib.request.Request('https://api.github.com/repos/'+repository+path,
            data=None if data is None else json.dumps(data).encode(), headers={'Authorization':'Bearer '+token,
            'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=30) as response:
                raw=response.read(2097153);require(len(raw)<=2097152,'API response size');return json.loads(raw)
        except urllib.error.HTTPError as error:
            if missing_ok and error.code == 404:
                return None
            raise RuntimeError('GitHub request failed with status '+str(error.code)) from None
    # Re-check label on the live issue. Edits still produce a draft PR and never bypass maintainer review.
    current=api('/issues/'+str(issue['number']))
    require(any(x.get('name')=='marketplace-submission' for x in current.get('labels',[])),'Label removed')
    package=extract(current.get('body',''))
    root=Path(__file__).resolve().parents[1]
    relative=package_path(package)
    data=encoded(package)
    target=root/relative
    require(not target.is_symlink(),'Symlink')
    if target.exists():
        old=validate(load(target.read_bytes()))
        require(package['version']>old['version'],'An update must increase the package version')
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    index=encoded(build_index(root)); (root/'index.json').write_bytes(index)
    base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    require(re.fullmatch('[0-9a-f]{40}',base),'Base commit')
    commit=api('/git/commits/'+base)
    branch='marketplace/issue-'+str(issue['number'])+'-'+hashlib.sha256(data).hexdigest()[:12]
    existing=api('/pulls?state=all&head='+urllib.parse.quote(repository.split('/')[0]+':'+branch,safe=''))
    if existing:
        print('This issue revision already has a pull request');return
    tree=api('/git/trees',{'base_tree':commit['tree']['sha'],'tree':[
        {'path':relative,'mode':'100644','type':'blob','content':data.decode()},
        {'path':'index.json','mode':'100644','type':'blob','content':index.decode()}]})
    # A transient failure or a disabled Actions PR permission can occur after the branch
    # is created. Retry safely, without overwriting somebody else's branch or duplicating PRs.
    ref=api('/git/ref/heads/'+branch, missing_ok=True)
    if ref is None:
        new_commit=api('/git/commits',{'message':'Review marketplace submission #'+str(issue['number']),'tree':tree['sha'],'parents':[base]})
        api('/git/refs',{'ref':'refs/heads/'+branch,'sha':new_commit['sha']})
    else:
        previous=api('/git/commits/'+ref['object']['sha'])
        require(previous['tree']['sha']==tree['sha'] and [p['sha'] for p in previous['parents']]==[base],
            'Existing proposal branch differs; maintainer review required')
    api('/pulls',{'title':'Review marketplace submission #'+str(issue['number']),'head':branch,
        'base':event['repository']['default_branch'],'draft':True,
        'body':'Generated from issue #'+str(issue['number'])+'. JSON validation is not a security audit. Review every action, network destination, permission and embedded script before marking ready and merging. Nothing has been executed.'})
    print('Draft pull request created; manual review and merge are required')

if __name__=='__main__':
    try:
        main()
    except Exception:
        # No user payloads, credentials or HTTP exception bodies in Actions logs.
        raise SystemExit('Submission rejected or GitHub operation failed. Review the issue and repository Actions permissions.')
