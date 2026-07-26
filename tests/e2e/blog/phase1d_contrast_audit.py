"""Attributed WCAG contrast audit for meaningful visible Blog UI."""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE = "http://127.0.0.1:5510"
RESULT = Path("/tmp/ampyan_phase1d_contrast.json")
PAGES = (
    ("listing", "/blogs"), ("detail", "/blogs/phase1d-published"),
    ("editor", "/blogs/2/edit"), ("my_blogs", "/blogs/me"),
    ("analytics", "/blogs/me/analytics"), ("moderation", "/blogs/moderation"),
)


def login(page, username):
    page.goto(BASE + "/login")
    page.get_by_label("Username or Email").fill(username)
    page.get_by_label("Password").fill("Phase1dPass!9")
    page.get_by_role("button", name="Login").press("Enter")
    page.wait_for_load_state("domcontentloaded")


def run():
    rows = []
    legacy_rows = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True, executable_path=os.environ.get("PHASE1D_CHROME_PATH") or None
        )
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        login(page, "author1")
        for state, path in PAGES:
            if state == "moderation":
                context.clear_cookies()
                login(page, "moderator")
            page.goto(BASE + path)
            page.wait_for_timeout(300)
            samples = page.evaluate(
                """({state}) => {
                  const parse = value => {
                    const n=(value.match(/[\\d.]+/g)||[]).map(Number);
                    return [n[0]||0,n[1]||0,n[2]||0,n.length>3?n[3]:1];
                  };
                  const blend=(top,bottom)=>[
                    top[0]*top[3]+bottom[0]*(1-top[3]),
                    top[1]*top[3]+bottom[1]*(1-top[3]),
                    top[2]*top[3]+bottom[2]*(1-top[3]),1
                  ];
                  const background=node=>{
                    let layers=[],current=node;
                    while(current){layers.push(parse(getComputedStyle(current).backgroundColor));current=current.parentElement;}
                    let result=[5,7,12,1];
                    for(let i=layers.length-1;i>=0;i--)result=blend(layers[i],result);
                    return result;
                  };
                  const lum=c=>{
                    const v=c.slice(0,3).map(x=>{x/=255;return x<=.04045?x/12.92:Math.pow((x+.055)/1.055,2.4)});
                    return .2126*v[0]+.7152*v[1]+.0722*v[2];
                  };
                  const selector=node=>{
                    if(node.id)return '#'+CSS.escape(node.id);
                    let value=node.tagName.toLowerCase();
                    if(node.classList.length)value+='.'+[...node.classList].slice(0,2).map(CSS.escape).join('.');
                    return value+`:nth-of-type(${[...node.parentElement.children].filter(x=>x.tagName===node.tagName).indexOf(node)+1})`;
                  };
                  const output=[];
                  for(const node of document.querySelectorAll('p,a,button,label,input,textarea,select,summary,strong,h1,h2,h3,.blog-status,.auth-flash')){
                    const rect=node.getBoundingClientRect(),style=getComputedStyle(node);
                    const name=(node.innerText||node.value||node.placeholder||node.getAttribute('aria-label')||'').trim();
                    if(!name||rect.width<1||rect.height<1||style.visibility==='hidden'||style.display==='none')continue;
                    const fg=parse(style.color),bg=background(node);
                    const ratio=(Math.max(lum(fg),lum(bg))+.05)/(Math.min(lum(fg),lum(bg))+.05);
                    const size=parseFloat(style.fontSize),weight=parseInt(style.fontWeight)||400;
                    const large=size>=24||(size>=18.66&&weight>=700);
                    const disabled=node.matches(':disabled');
                    const threshold=disabled?0:(large?3:4.5);
                    output.push({state,viewport:'1440x900',selector:selector(node),role:node.getAttribute('role')||node.tagName.toLowerCase(),text:name.slice(0,100),foreground:style.color,background:`rgb(${bg.slice(0,3).map(Math.round).join(', ')})`,opacity:style.opacity,font_size:size,font_weight:weight,ratio:+ratio.toFixed(2),required:threshold,pass:threshold===0||ratio>=threshold,disabled});
                  }
                  return output;
                }""",
                {"state": state},
            )
            rows.extend(samples)
            legacy_rows.extend(page.evaluate(
                """({state}) => {
                  function rgb(value){const m=value.match(/[\\d.]+/g);return m?m.slice(0,3).map(Number):[0,0,0]}
                  function lum(c){const x=c.map(v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)});return .2126*x[0]+.7152*x[1]+.0722*x[2]}
                  const output=[];
                  for(const node of document.querySelectorAll('body,h1,h2,p,a,button,label,input,textarea')){
                    if(!node.offsetParent||output.length>=30)continue;
                    const s=getComputedStyle(node),fg=lum(rgb(s.color));let parent=node,bg='rgba(0, 0, 0, 0)';
                    while(parent&&(bg==='rgba(0, 0, 0, 0)'||bg==='transparent')){bg=getComputedStyle(parent).backgroundColor;parent=parent.parentElement}
                    const bl=lum(rgb(bg)),ratio=(Math.max(fg,bl)+.05)/(Math.min(fg,bl)+.05);
                    output.push({state,tag:node.tagName,text:(node.innerText||node.value||'').slice(0,60),foreground:s.color,background:bg,ratio:+ratio.toFixed(2),disabled:node.matches(':disabled')});
                  }return output;
                }""", {"state": state}
            ))
        context.close()
        browser.close()
    RESULT.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    failures = [row for row in rows if not row["pass"]]
    lowest = sorted(rows, key=lambda row: row["ratio"])[:10]
    legacy_lowest = sorted(legacy_rows, key=lambda row: row["ratio"])[:10]
    print(json.dumps({
        "samples": len(rows), "failures": len(failures),
        "lowest": lowest, "legacy_lowest": legacy_lowest,
        "failure_examples": failures[:20],
        "result_file": str(RESULT),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run()
