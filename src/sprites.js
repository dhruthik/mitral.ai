const OUTLINE = '#241e38';
const pick = values => values[Math.floor(Math.random() * values.length)];

const TEMPLATES = {
  dreamer: {
    palette: { h:'#5b3fc4',H:'#7c5ce8',s:'#e8b88a',c:'#9d85f2',e:OUTLINE,m:'#b4543e',a:'#ffd8fe',k:OUTLINE,w:'#fff' },
    idle:['.a...hh...a.','..hhHHHHhh..','.hHHHHHHHHh.','.hHssssssHh.','.hHewssweHh.','.hHssssssHh.','..ssmmssss..','...ssssss...','..hcccccch..','.sccccccccs.','.sccccccccs.','..cccccccc..','..cccccccc..','...cc..cc...','..kk....kk..','............'],
    blink:{4:'.hHkssskkHh.'}, talk:{6:'..ssmmmmss..',7:'...smmmms...'},
  },
  skeptic: {
    palette: { h:'#4a4238',s:'#efcfaf',c:'#64748b',e:OUTLINE,m:OUTLINE,k:OUTLINE,w:'#fff' },
    idle:['............','..hhhhhhhh..','..hhhhhhhh..','..kkssssss..','..sesskkss..','..sesssess..','..ssssssss..','..ssmmmmss..','...ssssss...','..cccccccc..','.ccsssssscc.','.ccsssssscc.','..cccccccc..','...cc..cc...','..kk....kk..','............'],
    blink:{5:'..skssskss..'}, talk:{7:'..ssmmmsss..',8:'...smmsss...'},
  },
  pragmatist: {
    palette: { a:'#e09a2f',A:'#b87716',s:'#a9714b',c:'#3e5c76',e:OUTLINE,m:OUTLINE,g:'#9aa3ae',k:OUTLINE,w:'#fff' },
    idle:['...aaaaaa...','..aaaaaaaa..','.AAAAAAAAAA.','..ssssssss..','..sesssses..','..ssssssss..','..ssssmmss..','...ssssss...','..ccccccccg.','.sccccccccg.','.sccccccccg.','..cccccccc..','..cccccccc..','...cc..cc...','..kk....kk..','............'],
    blink:{4:'..skssssks..'}, talk:{6:'..sssmmmss..',7:'...ssmmss...'},
  },
  advocate: {
    palette: { h:'#2a2135',s:'#7a4a32',c:'#e86a8a',e:OUTLINE,m:'#4a1d12',k:OUTLINE,w:'#fff' },
    idle:['.hh......hh.','.hhhhhhhhhh.','..hhhhhhhh..','..ssssssss..','..sewssews..','..ssssssss..','..ssmmmmss..','...ssssss.s.','..ccccccccs.','.scccccccc..','.scccccccc..','..cccccccc..','..cccccccc..','...cc..cc...','..kk....kk..','............'],
    blink:{4:'..skssssks..'}, talk:{6:'..smmmmmms..',7:'...smmmms.s.'},
  },
  wildcard: {
    palette: { s:'#3ecdba',a:'#ffd166',c:'#2b6e80',e:OUTLINE,m:OUTLINE,k:OUTLINE,w:'#fff' },
    idle:['.....aa.....','......a.....','..ssssssss..','.ssssssssss.','.sseesssess.','.ssssssssss.','..smsmsmss..','..ssssssss..','..cccccccc..','.sccccccccww','..ccccccccww','..cccccccc..','..cccccccc..','...ss..ss...','..kk....kk..','............'],
    blink:{4:'.sskkssskss.'}, talk:{6:'..smmmmmss..',7:'..ssmmmmss..'},
  },
};

const SKINS = ['#e8b88a','#efcfaf','#c68b59','#a9714b','#7a4a32'];
const CREATURE_SKINS = ['#3ecdba','#b39ddb','#f48fb1','#8fd46a'];
const HAIR = [['#4a4238','#6b5f4e'],['#2a2135','#4a3b5c'],['#5b3fc4','#7c5ce8'],['#b4432f','#d96a4a'],['#26547c','#3e7cb1'],['#1e7a5a','#35a57e']];
const CLOTHES = ['#9d85f2','#64748b','#3e5c76','#e86a8a','#2b6e80','#c05c4e','#5c8a4e','#7a5cb8'];
const CAPS = [['#e09a2f','#b87716'],['#4c9be0','#2f6fa8'],['#e85c7a','#b23a54'],['#5cb85c','#3e8a3e']];

export function makeSprite(stance) {
  const template = TEMPLATES[stance];
  const palette = { ...template.palette, c: pick(CLOTHES) };
  if (stance === 'wildcard') palette.s = pick(CREATURE_SKINS);
  else {
    palette.s = pick(SKINS);
    if (palette.h) [palette.h, palette.H] = pick(HAIR);
    if (stance === 'pragmatist') [palette.a, palette.A] = pick(CAPS);
  }
  return { ...template, palette };
}

export function drawSprite(canvas, sprite, frame = 'idle') {
  const context = canvas.getContext('2d');
  const overrides = sprite[frame] || {};
  context.clearRect(0, 0, 12, 16);
  sprite.idle.forEach((baseRow, y) => {
    const row = overrides[y] || baseRow;
    [...row].forEach((pixel, x) => {
      if (!sprite.palette[pixel]) return;
      context.fillStyle = sprite.palette[pixel];
      context.fillRect(x, y, 1, 1);
    });
  });
}
