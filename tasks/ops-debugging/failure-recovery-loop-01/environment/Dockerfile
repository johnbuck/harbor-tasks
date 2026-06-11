FROM harbor-agents-rich:latest
WORKDIR /app

# Adaptive-recovery tool `dfetch`: fails with DIFFERENT, actionable errors until
# the agent reads each one and applies the SPECIFIC fix (supply --region, then a
# provisioned region, then a valid --token, then clear a stale lock via `dfetch
# --release`). A blind retry of the same command stalls on the first unmet
# requirement forever, so CORRECTNESS itself discriminates an adaptive harness.
# The errors name the failing FLAG but not the VALUE: the provisioned regions and
# the session token are DISCOVERED from /app/dfetch.conf, not dictated by stderr.
#
# FORGERY-PROOF SUCCESS (rebuild 2026-06-11). dfetch is a COMPILED, STRIPPED C
# binary. On a genuine success it mints NONCE = HMAC-SHA256(secret,
# region|token|counter), where the 32-byte secret is generated at build time and
# embedded XOR-masked into the binary; the .c and the secret header are removed in
# the SAME layer, so no plaintext secret survives in the image. Because the agent
# runs as root and shares the filesystem with the post-agent verifier, no secret
# FILE could be hidden from it and the grader could not hold a secret the agent
# cannot read -- so authentication is delegated to the binary itself via a hidden
# `dfetch --verify <msg> <nonce>` subcommand (exit 0 only for an authentic nonce).
# Every rejected call appends its stage to the ordered append-only progression log
# /var/log/dfetch.progression (bad-region -> 401 -> stale-lock -> release); the
# verifier requires that ordered trail PLUS a verified nonce, so a forged
# STATUS=success scores 0 at ANY call count.
# RESIDUAL: a root agent could strings/disassemble the stripped binary to recover
# the secret; "no secret FILE on the fs" is proven, RE-resistance is the design bet
# (the honest error-walk is strictly shorter). See remediation D1.

# Compile dfetch from C with a build-time random secret, strip it, and delete the
# source + secret header IN THE SAME LAYER so neither survives in the image.
RUN sh <<'DFBUILD'
set -eu
if ! command -v gcc >/dev/null 2>&1; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends gcc libc6-dev
  rm -rf /var/lib/apt/lists/*
fi
SEC=$(head -c32 /dev/urandom | od -An -tx1 | tr -d '[:space:]')
python3 - "$SEC" > /tmp/dfetch_secret.h <<'GENPY'
import sys
sec = bytes.fromhex(sys.argv[1])
XOR = 0x5a
print("#define SECRET_LEN %d" % len(sec))
print("static const unsigned char SECRET_OBF[SECRET_LEN] = {%s};" % ",".join(str(b ^ XOR) for b in sec))
print("#define SECRET_XOR 0x5a")
GENPY
cat > /tmp/dfetch.c <<'CSOURCE'
/* dfetch — adaptive-recovery tool with an HMAC-authenticated success nonce.
 *
 * The success NONCE is HMAC-SHA256(secret, "region|token|counter"), where the
 * 32-byte secret is generated at image build and embedded (XOR-masked) into THIS
 * binary, which is then stripped. No plaintext secret survives in the image, so a
 * root agent cannot forge a valid nonce by reading a file: the only way to mint a
 * passing nonce is to drive dfetch through the real error ladder to a genuine
 * success. A hidden `dfetch --verify <msg> <nonce>` subcommand lets the verifier
 * re-check a nonce WITHOUT ever holding the secret (which it could not hide from
 * the agent on the shared filesystem anyway).
 *
 * Every rejected call appends its stage to the append-only ordered progression
 * log /var/log/dfetch.progression (bad-region -> 401 -> stale-lock -> release),
 * so a genuine recovery leaves a mechanical trail the verifier requires.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "dfetch_secret.h"   /* SECRET_OBF[SECRET_LEN], SECRET_XOR */

/* ---- SHA-256 (public-domain style, compact) ------------------------------ */
typedef struct { uint32_t s[8]; uint64_t n; unsigned char buf[64]; size_t len; } sha256_t;

static uint32_t rotr(uint32_t x, int c) { return (x >> c) | (x << (32 - c)); }

static const uint32_t K[64] = {
0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};

static void sha256_init(sha256_t *ctx) {
    ctx->s[0]=0x6a09e667; ctx->s[1]=0xbb67ae85; ctx->s[2]=0x3c6ef372; ctx->s[3]=0xa54ff53a;
    ctx->s[4]=0x510e527f; ctx->s[5]=0x9b05688c; ctx->s[6]=0x1f83d9ab; ctx->s[7]=0x5be0cd19;
    ctx->n=0; ctx->len=0;
}
static void sha256_block(sha256_t *ctx, const unsigned char *p) {
    uint32_t w[64], a,b,c,d,e,f,g,h,t1,t2; int i;
    for (i=0;i<16;i++) w[i]=(p[i*4]<<24)|(p[i*4+1]<<16)|(p[i*4+2]<<8)|p[i*4+3];
    for (i=16;i<64;i++) {
        uint32_t s0=rotr(w[i-15],7)^rotr(w[i-15],18)^(w[i-15]>>3);
        uint32_t s1=rotr(w[i-2],17)^rotr(w[i-2],19)^(w[i-2]>>10);
        w[i]=w[i-16]+s0+w[i-7]+s1;
    }
    a=ctx->s[0];b=ctx->s[1];c=ctx->s[2];d=ctx->s[3];
    e=ctx->s[4];f=ctx->s[5];g=ctx->s[6];h=ctx->s[7];
    for (i=0;i<64;i++) {
        uint32_t S1=rotr(e,6)^rotr(e,11)^rotr(e,25);
        uint32_t ch=(e&f)^((~e)&g);
        t1=h+S1+ch+K[i]+w[i];
        uint32_t S0=rotr(a,2)^rotr(a,13)^rotr(a,22);
        uint32_t maj=(a&b)^(a&c)^(b&c);
        t2=S0+maj;
        h=g; g=f; f=e; e=d+t1; d=c; c=b; b=a; a=t1+t2;
    }
    ctx->s[0]+=a;ctx->s[1]+=b;ctx->s[2]+=c;ctx->s[3]+=d;
    ctx->s[4]+=e;ctx->s[5]+=f;ctx->s[6]+=g;ctx->s[7]+=h;
}
static void sha256_update(sha256_t *ctx, const unsigned char *p, size_t n) {
    ctx->n += n;
    while (n) {
        size_t k = 64 - ctx->len; if (k > n) k = n;
        memcpy(ctx->buf + ctx->len, p, k); ctx->len += k; p += k; n -= k;
        if (ctx->len == 64) { sha256_block(ctx, ctx->buf); ctx->len = 0; }
    }
}
static void sha256_final(sha256_t *ctx, unsigned char out[32]) {
    uint64_t bits = ctx->n * 8; unsigned char pad = 0x80; int i;
    sha256_update(ctx, &pad, 1);
    unsigned char z = 0;
    while (ctx->len != 56) sha256_update(ctx, &z, 1);
    unsigned char lb[8];
    for (i=0;i<8;i++) lb[i] = (unsigned char)(bits >> (56 - i*8));
    sha256_update(ctx, lb, 8);
    for (i=0;i<8;i++) { out[i*4]=ctx->s[i]>>24; out[i*4+1]=ctx->s[i]>>16; out[i*4+2]=ctx->s[i]>>8; out[i*4+3]=ctx->s[i]; }
}

/* ---- HMAC-SHA256 -> hex --------------------------------------------------- */
static void hmac_sha256_hex(const unsigned char *key, size_t klen,
                            const char *msg, char hexout[65]) {
    unsigned char k[64], ipad[64], opad[64], ih[32], oh[32];
    size_t i, mlen = strlen(msg);
    memset(k, 0, 64);
    if (klen > 64) {
        sha256_t c; sha256_init(&c); sha256_update(&c, key, klen); sha256_final(&c, k);
    } else memcpy(k, key, klen);
    for (i=0;i<64;i++) { ipad[i]=k[i]^0x36; opad[i]=k[i]^0x5c; }
    sha256_t c; sha256_init(&c); sha256_update(&c, ipad, 64);
    sha256_update(&c, (const unsigned char *)msg, mlen); sha256_final(&c, ih);
    sha256_init(&c); sha256_update(&c, opad, 64); sha256_update(&c, ih, 32); sha256_final(&c, oh);
    for (i=0;i<32;i++) sprintf(hexout + i*2, "%02x", oh[i]);
    hexout[64] = '\0';
}

static void load_secret(unsigned char out[SECRET_LEN]) {
    int i;
    for (i=0;i<SECRET_LEN;i++) out[i] = SECRET_OBF[i] ^ SECRET_XOR;
}

/* ---- dfetch logic --------------------------------------------------------- */
/* DF_PREFIX is empty in the shipped binary (absolute /var/log + /app); it exists
 * only so the build/test harness can compile a path-prefixed variant. */
#ifndef DF_PREFIX
#define DF_PREFIX ""
#endif
#define CTR  DF_PREFIX "/var/log/dfetch.counter"
#define ST   DF_PREFIX "/var/log/dfetch.state"
#define LOCK DF_PREFIX "/var/log/dfetch.lock"
#define PROG DF_PREFIX "/var/log/dfetch.progression"
#define CONF DF_PREFIX "/app/dfetch.conf"

static void append_stage(const char *stage) {
    FILE *f = fopen(PROG, "a");
    if (f) { fprintf(f, "%s\n", stage); fclose(f); }
}

static long bump_counter(void) {
    long n = 0; FILE *f = fopen(CTR, "r");
    if (f) { if (fscanf(f, "%ld", &n) != 1) n = 0; fclose(f); }
    n += 1;
    f = fopen(CTR, "w"); if (f) { fprintf(f, "%ld\n", n); fclose(f); }
    return n;
}

/* Read a "key=value" line from CONF, return 1 if value matches `want` for key. */
static int conf_has(const char *key, const char *want) {
    char line[512]; FILE *f = fopen(CONF, "r"); if (!f) return 0;
    size_t klen = strlen(key); int found = 0;
    while (fgets(line, sizeof line, f)) {
        char *nl = strchr(line, '\n'); if (nl) *nl = '\0';
        if (strncmp(line, key, klen) == 0 && line[klen] == '=' &&
            strcmp(line + klen + 1, want) == 0) { found = 1; break; }
    }
    fclose(f); return found;
}

static int conf_get(const char *key, char *out, size_t outsz) {
    char line[512]; FILE *f = fopen(CONF, "r"); if (!f) return 0;
    size_t klen = strlen(key); int found = 0;
    while (fgets(line, sizeof line, f)) {
        char *nl = strchr(line, '\n'); if (nl) *nl = '\0';
        if (strncmp(line, key, klen) == 0 && line[klen] == '=') {
            strncpy(out, line + klen + 1, outsz - 1); out[outsz - 1] = '\0'; found = 1; break;
        }
    }
    fclose(f); return found;
}

int main(int argc, char **argv) {
    unsigned char secret[SECRET_LEN];
    load_secret(secret);

    /* Hidden verify subcommand: dfetch --verify <msg> <nonce> -> exit 0 if the
     * nonce is the authentic HMAC of msg. Does NOT touch counter/state/log. */
    if (argc >= 4 && strcmp(argv[1], "--verify") == 0) {
        char want[65]; hmac_sha256_hex(secret, SECRET_LEN, argv[2], want);
        return (strcmp(want, argv[3]) == 0) ? 0 : 1;
    }

    long calls = bump_counter();

    const char *region = NULL, *token = NULL, *out = NULL; int release = 0;
    for (int i = 1; i < argc; i++) {
        if (strncmp(argv[i], "--region=", 9) == 0) region = argv[i] + 9;
        else if (strncmp(argv[i], "--token=", 8) == 0) token = argv[i] + 8;
        else if (strcmp(argv[i], "--release") == 0) release = 1;
        else if (strncmp(argv[i], "--", 2) == 0) { /* ignore */ }
        else out = argv[i];
    }

    if (release) {
        FILE *f = fopen(LOCK, "w"); if (f) { fprintf(f, "released\n"); fclose(f); }
        append_stage("release");
        fprintf(stderr, "dfetch: lock released\n");
        return 0;
    }
    if (!region || !*region) {
        append_stage("bad-region");
        fprintf(stderr, "dfetch: error: --region is required\n");
        return 2;
    }
    if (!conf_has("provisioned_region", region)) {
        append_stage("bad-region");
        fprintf(stderr, "dfetch: error: region '%s' is not provisioned\n", region);
        return 2;
    }
    if (!token || !*token) {
        append_stage("401");
        fprintf(stderr, "dfetch: error: 401 unauthorized; provide a valid session token via --token\n");
        return 3;
    }
    char valid[256];
    if (!conf_get("session_token", valid, sizeof valid) || strcmp(token, valid) != 0) {
        append_stage("401");
        fprintf(stderr, "dfetch: error: 401 unauthorized; supplied session token is not valid\n");
        return 3;
    }
    {
        char lk[64] = ""; FILE *f = fopen(LOCK, "r");
        if (f) { if (fgets(lk, sizeof lk, f)) { char *nl = strchr(lk, '\n'); if (nl) *nl = '\0'; } fclose(f); }
        if (strcmp(lk, "released") != 0) {
            append_stage("stale-lock");
            fprintf(stderr, "dfetch: error: a stale lock from a previous run is held; release it before fetching\n");
            return 4;
        }
    }
    if (!out || !*out) {
        fprintf(stderr, "dfetch: error: no output path given\n");
        return 5;
    }

    /* Genuine success: mint the authenticated nonce. */
    char msg[1024], nonce[65];
    snprintf(msg, sizeof msg, "%s|%s|%ld", region, token, calls);
    hmac_sha256_hex(secret, SECRET_LEN, msg, nonce);

    FILE *s = fopen(ST, "w");
    if (s) { fprintf(s, "STATUS=success\nNONCE=%s\nMSG=%s\n", nonce, msg); fclose(s); }
    FILE *o = fopen(out, "w");
    if (o) { fprintf(o, "PAYLOAD: %s\n", nonce); fclose(o); }
    fprintf(stderr, "dfetch: success\n");
    return 0;
}
CSOURCE
gcc -O2 -I/tmp -o /usr/local/bin/dfetch /tmp/dfetch.c
strip /usr/local/bin/dfetch
chmod 755 /usr/local/bin/dfetch
rm -f /tmp/dfetch.c /tmp/dfetch_secret.h
# AUTHENTICATOR INTEGRITY PIN (criterion 1). The grader (tests/test.sh) trusts the
# dfetch binary for HMAC verification, but a root agent could swap it for an
# exit-0 stub. The grader therefore requires the binary's sha256 to match a digest
# PINNED in the trusted post-agent grader. Capture that digest here and paste it
# into tests/test.sh's EXPECTED_DFETCH_SHA (the D7 build step). The secret — hence
# the binary — is randomised per build, so the digest can only be known after this
# build; it is printed to the build log AND written to a build-artifact file.
DFETCH_SHA="$(sha256sum /usr/local/bin/dfetch | cut -d' ' -f1)"
printf '%s\n' "$DFETCH_SHA" > /usr/local/share/dfetch.sha256
echo ">>> dfetch sha256 = ${DFETCH_SHA}"
echo ">>> D7: paste this into tasks/.../tests/test.sh EXPECTED_DFETCH_SHA before the sweep"
DFBUILD

# Provisioning manifest the agent DISCOVERS by exploring /app (the errors point at
# the flags but never at these values). Single source of truth: dfetch reads the
# provisioned regions + the session token from here.
RUN cat > /app/dfetch.conf <<'EOF'
# dfetch provisioning manifest
# Regions provisioned for this account (any other region is rejected):
provisioned_region=eu-west
provisioned_region=us-east
# Session token required for authenticated fetches:
session_token=sk-fetch-9f3a2b71
EOF

RUN mkdir -p /var/log && printf '0\n' > /var/log/dfetch.counter
