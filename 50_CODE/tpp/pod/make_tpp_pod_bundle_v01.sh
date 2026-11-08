#!/usr/bin/env bash
# make_tpp_pod_bundle_v01.sh (laptop, Git Bash): packs what run_tpp_pod_v01.sh needs, with paths relative to W so the
# code's relative imports hold on the pod: the TPP code and tests, k8_items_v02.py and k6_sim_v02.py (imported read-only
# by the keys), the Trajectron++ checkout without .git, the two val caches, and the laptop spot-check reference.
# Writes 50_CODE/tpp/pod/BUNDLE_SHA256SUMS_v01.txt (verified on the pod) and TPP_POD_BUNDLE_v01.tar.gz + .sha256.
set -euo pipefail
WB="/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
cd "$WB"
P=50_CODE/tpp/pod
{ ls 50_CODE/tpp/*.py 50_CODE/tpp/TPP_PROVENANCE_v01.txt 50_CODE/tpp/tests/*.py
  ls $P/run_tpp_pod_v01.sh $P/requirements_tpp38_v01.txt $P/requirements_keys310_v01.txt
  ls 50_CODE/k8/k8_items_v02.py 50_CODE/k6/k6_sim_v02.py
  find 50_CODE/third_party/Trajectron-plus-plus_eccv2020 -type f -not -path '*/.git/*' | sort
  ls 30_DATA/k6/cache_v02_t1_val/* 30_DATA/k6/cache_v02_t3_val/*
  ls 70_TESTS/tpp_v01/xplat_laptop/*.npz; } > "$P/bundle_files_v01.txt"
xargs -d '\n' sha256sum < "$P/bundle_files_v01.txt" > "$P/BUNDLE_SHA256SUMS_v01.txt"
tar -czf "$P/TPP_POD_BUNDLE_v01.tar.gz" -T "$P/bundle_files_v01.txt" "$P/BUNDLE_SHA256SUMS_v01.txt" "$P/bundle_files_v01.txt"
sha256sum "$P/TPP_POD_BUNDLE_v01.tar.gz" > "$P/TPP_POD_BUNDLE_v01.tar.gz.sha256"
echo "files: $(wc -l < "$P/bundle_files_v01.txt")  size: $(du -h "$P/TPP_POD_BUNDLE_v01.tar.gz" | cut -f1)"
cat "$P/TPP_POD_BUNDLE_v01.tar.gz.sha256"
