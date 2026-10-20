// Clash Mi JS 覆写（自动生成，请勿手改；源文件 overwrite/Clash_Mi_Merge.yaml，生成脚本 scripts/build_clashmi_js.py）
// 用法：Clash Mi「覆写」里新增 URL 覆写，类型选 js，地址填
//   https://testingcf.jsdelivr.net/gh/mrc991/lc-network-rules@main/overwrite/Clash_Mi_Merge.js
// 并在订阅设置里把覆写从 Clash_Mi_Merge.yaml 换成它。YAML 覆写不支持 prepend-rules，所以必须用 JS。
// 语义：与 YAML 覆写一致（字典深合并，列表/标量整体替换），另把 LC_PREPEND_RULES 插到 rules 最前。
var LC_PATCH = {
  "rule-providers": {
    "lc-adblock-domain": {
      "type": "http",
      "behavior": "domain",
      "format": "yaml",
      "url": "https://testingcf.jsdelivr.net/gh/mrc991/lc-network-rules@main/overwrite/adblock/AdBlock_Domain.yaml",
      "path": "./ruleset/lc_adblock_domain.yaml",
      "interval": 86400
    },
    "lc-adblock-ip": {
      "type": "http",
      "behavior": "ipcidr",
      "format": "yaml",
      "url": "https://testingcf.jsdelivr.net/gh/mrc991/lc-network-rules@main/overwrite/adblock/AdBlock_IP.yaml",
      "path": "./ruleset/lc_adblock_ip.yaml",
      "interval": 86400
    }
  },
  "ipv6": false,
  "find-process-mode": "always",
  "external-ui-url": "",
  "global-client-fingerprint": "chrome",
  "keep-alive-idle": 30,
  "keep-alive-interval": 30,
  "dns": {
    "enable": true,
    "prefer-h3": false,
    "ipv6": false,
    "ipv6-timeout": 300,
    "enhanced-mode": "fake-ip",
    "fake-ip-range": "198.18.0.1/16",
    "cache-algorithm": "arc",
    "default-nameserver": [
      "223.5.5.5",
      "119.29.29.29"
    ],
    "nameserver": [
      "https://223.5.5.5/dns-query",
      "https://1.12.12.12/dns-query"
    ],
    "fallback": [],
    "respect-rules": false,
    "nameserver-policy": {
      "geosite:cn": [
        "https://223.5.5.5/dns-query",
        "https://1.12.12.12/dns-query"
      ],
      "geosite:geolocation-!cn": [
        "https://223.5.5.5/dns-query",
        "https://1.12.12.12/dns-query"
      ]
    },
    "proxy-server-nameserver": [
      "223.5.5.5",
      "119.29.29.29"
    ],
    "fake-ip-filter": [
      "+.qpic.cn",
      "+.qlogo.cn",
      "+.wechatos.net",
      "+.weixin.qq.com",
      "+.wechat.com",
      "+.weixin.com",
      "+.servicewechat.com",
      "+.tenpay.com",
      "+.gtimg.cn",
      "+.idqqimg.com",
      "+.tencent-cloud.net",
      "+.qq.com",
      "+.tencent.com",
      "localhost.ptlogin2.qq.com",
      "localhost.sec.qq.com",
      "localhost.*.weixin.qq.com",
      "+.tailscale.com",
      "+.tailscale.io",
      "+.ts.net",
      "+.heiyu.space",
      "+.lazycat.cloud",
      "+.bigrich.cc",
      "+.quickconnect.to",
      "+.quickconnect.cn",
      "+.synology.com",
      "+.synology.cn",
      "+.synology.me",
      "BigRichNAS",
      "BigRichNAS.local",
      "+.anydesk.com",
      "+.net.anydesk.com",
      "+.anydesk.com.cn",
      "+.net.anydesk.com.cn",
      "localhost",
      "WORKGROUP",
      "+.lan",
      "+.local",
      "+.localdomain",
      "+.home.arpa",
      "+.direct",
      "+.example",
      "+.invalid",
      "+.test",
      "time.*.com",
      "time.*.gov",
      "time.*.edu.cn",
      "time.*.apple.com",
      "time-ios.apple.com",
      "time[1-7].*.com",
      "ntp.*.com",
      "ntp[1-7].*.com",
      "+.time.edu.cn",
      "+.ntp.org.cn",
      "+.pool.ntp.org",
      "time1.cloud.tencent.com",
      "+.music.163.com",
      "music.163.com",
      "+.126.net",
      "+.y.qq.com",
      "y.qq.com",
      "streamoc.music.tc.qq.com",
      "mobileoc.music.tc.qq.com",
      "isure.stream.qqmusic.qq.com",
      "dl.stream.qqmusic.qq.com",
      "aqqmusic.tc.qq.com",
      "amobile.music.tc.qq.com",
      "+.kuwo.cn",
      "songsearch.kugou.com",
      "trackercdn.kugou.com",
      "musicapi.taihe.com",
      "music.taihe.com",
      "+.xiami.com",
      "+.music.migu.cn",
      "music.migu.cn",
      "api.joox.com",
      "joox.com",
      "api-jooxtt.sanook.com",
      "+.srv.nintendo.net",
      "+.cdn.nintendo.net",
      "+.stun.playstation.net",
      "xbox.*.*.microsoft.com",
      "xbox.*.microsoft.com",
      "+.xboxlive.com",
      "xnotify.xboxlive.com",
      "+.battle.net",
      "+.battlenet.com.cn",
      "+.wotgame.cn",
      "+.wggames.cn",
      "+.wowsgame.cn",
      "+.wargaming.net",
      "+.square-enix.com",
      "+.finalfantasyxiv.com",
      "+.ffxiv.com",
      "+.ff14.sdo.com",
      "ff.dorado.sdo.com",
      "+.blzstatic.cn",
      "+.services.googleapis.cn",
      "lens.l.google.com",
      "stun.l.google.com",
      "na.b.g-tun.com",
      "+.push.apple.com",
      "mesu.apple.com",
      "swscan.apple.com",
      "swquery.apple.com",
      "swdownload.apple.com",
      "swcdn.apple.com",
      "swdist.apple.com",
      "+.msftncsi.com",
      "+.msftconnecttest.com",
      "+.market.xiaomi.com",
      "Mijia Cloud",
      "+.adguard.org",
      "local.adguard.org",
      "+.cmbchina.com",
      "+.cmbimg.com",
      "+.pingan.com.cn",
      "+.cmpassport.com",
      "id6.me",
      "open.e.189.cn",
      "opencloud.wostore.cn",
      "id.mail.wo.cn",
      "hmrz.wo.cn",
      "nishub1.10010.com",
      "+.wosms.cn",
      "+.jegotrip.com.cn",
      "+.nflxvideo.net",
      "+.media.dssott.com",
      "+.sandai.net",
      "+.n0808.com",
      "+.uu.163.com",
      "ps.res.netease.com",
      "stun.*.*",
      "stun.*.*.*",
      "+.stun.*.*",
      "+.pub.3gppnetwork.org",
      "proxy.golang.org",
      "router.asus.com",
      "+.linksys.com",
      "+.linksyssmartwifi.com",
      "PDC._msDCS.*.*",
      "DC._msDCS.*.*",
      "GC._msDCS.*.*",
      "network-test.debian.org",
      "detectportal.firefox.com",
      "geosite:category-games",
      "geosite:apple-cn"
    ]
  },
  "tun": {
    "enable": true,
    "stack": "system",
    "inet4-address": [
      "172.19.0.1/30"
    ],
    "dns-hijack": [
      "any:53"
    ],
    "strict-route": false,
    "auto-detect-interface": true,
    "disable-icmp-forwarding": false,
    "auto-route": true,
    "mtu": 1420
  },
  "sniffer": {
    "enable": true,
    "override-destination": true,
    "force-dns-mapping": true,
    "parse-pure-ip": true,
    "sniff": {
      "TLS": {
        "ports": [
          443,
          8443
        ]
      },
      "HTTP": {
        "ports": [
          80,
          "8080-8880"
        ],
        "override-destination": true
      },
      "QUIC": {
        "ports": [
          443
        ]
      }
    }
  }
};
var LC_PREPEND_RULES = [
  "AND,((NETWORK,udp),(DST-PORT,443)),REJECT",
  "PROCESS-NAME,cloud-drive-daemon,DIRECT",
  "PROCESS-NAME,cloud-drive-connect,DIRECT",
  "PROCESS-NAME,cloud-drive-ui,DIRECT",
  "PROCESS-NAME,cloud-drive-eventd,DIRECT",
  "PROCESS-NAME,SynologyDrive,DIRECT",
  "PROCESS-NAME,SynologyDriveClient,DIRECT",
  "DOMAIN-SUFFIX,quickconnect.to,DIRECT",
  "DOMAIN-SUFFIX,quickconnect.cn,DIRECT",
  "DOMAIN-SUFFIX,synology.com,DIRECT",
  "DOMAIN-SUFFIX,synology.cn,DIRECT",
  "DOMAIN-SUFFIX,synology.me,DIRECT",
  "DOMAIN,BigRichNAS,DIRECT",
  "DOMAIN-SUFFIX,BigRichNAS.local,DIRECT",
  "IP-CIDR,192.168.8.8/32,DIRECT,no-resolve",
  "PROCESS-NAME,AnyDesk,DIRECT",
  "PROCESS-NAME,AnyDesk.exe,DIRECT",
  "DOMAIN-SUFFIX,anydesk.com,DIRECT",
  "DOMAIN-SUFFIX,net.anydesk.com,DIRECT",
  "DOMAIN-SUFFIX,anydesk.com.cn,DIRECT",
  "DOMAIN-SUFFIX,net.anydesk.com.cn,DIRECT",
  "RULE-SET,lc-adblock-domain,REJECT",
  "RULE-SET,lc-adblock-ip,REJECT,no-resolve"
];

function lcIsMap(v) {
  return v !== null && typeof v === "object" && !Array.isArray(v);
}

function lcMerge(dst, src) {
  for (var k in src) {
    if (!Object.prototype.hasOwnProperty.call(src, k)) continue;
    if (lcIsMap(dst[k]) && lcIsMap(src[k])) {
      lcMerge(dst[k], src[k]);
    } else {
      dst[k] = JSON.parse(JSON.stringify(src[k]));
    }
  }
  return dst;
}

function main(config) {
  if (!lcIsMap(config)) config = {};
  lcMerge(config, LC_PATCH);
  var old = Array.isArray(config.rules) ? config.rules : [];
  var seen = {};
  var rules = [];
  var i;
  for (i = 0; i < LC_PREPEND_RULES.length; i++) {
    seen[LC_PREPEND_RULES[i]] = true;
    rules.push(LC_PREPEND_RULES[i]);
  }
  for (i = 0; i < old.length; i++) {
    if (!seen[old[i]]) rules.push(old[i]);
  }
  config.rules = rules;
  return config;
}
