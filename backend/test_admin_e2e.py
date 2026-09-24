import httpx
import sys

BASE_URL = "http://localhost:8000"

def main():
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        print("--- 1. Testing Admin Authentication ---")
        login_res = client.post("/api/v1/auth/login", json={
            "email": "admin@docassistiq.com",
            "password": "AdminSecure2026!"
        })
        if login_res.status_code != 200:
            print(f"FAILED to login: {login_res.status_code} {login_res.text}")
            sys.exit(1)
        
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Logged in successfully as Admin.")

        print("\n--- 2. Testing /admin/stats and /ready ---")
        stats_res = client.get("/api/v1/admin/stats", headers=headers)
        assert stats_res.status_code == 200, f"Stats failed: {stats_res.text}"
        print("Admin Stats:", stats_res.json())

        ready_res = client.get("/ready")
        assert ready_res.status_code == 200, f"Ready failed: {ready_res.text}"
        print("Ready Status:", ready_res.json()["status"])

        print("\n--- 3. Testing Doctors Pending & Verification ---")
        docs_res = client.get("/api/v1/doctors/pending?page=1&page_size=10", headers=headers)
        assert docs_res.status_code == 200, f"List pending doctors failed: {docs_res.text}"
        docs = docs_res.json()["items"]
        print(f"Found {len(docs)} pending doctors.")
        assert len(docs) > 0, "No pending doctors found!"
        first_doc = docs[0]
        verify_res = client.post(f"/api/v1/doctors/{first_doc['id']}/verify", json={"action": "verify"}, headers=headers)
        assert verify_res.status_code == 200, f"Verify doctor failed: {verify_res.text}"
        print(f"Verified doctor {first_doc['id']}: status is now {verify_res.json()['verification_status']}")

        print("\n--- 4. Testing Sources Registry & Verification ---")
        sources_res = client.get("/api/v1/sources/?page=1&page_size=20", headers=headers)
        assert sources_res.status_code == 200, f"List sources failed: {sources_res.text}"
        sources = sources_res.json()["items"]
        print(f"Found {len(sources)} sources.")
        
        # Create a new source
        new_source_res = client.post("/api/v1/sources/", json={
            "code": f"test_source_{first_doc['id'][:6]}",
            "name": "Test Clinical Research Registry",
            "organisation": "Clinical Research Institute",
            "access_mechanism": "api",
            "data_type": "clinical_guidelines",
            "license_info": "Open Database License"
        }, headers=headers)
        assert new_source_res.status_code in (200, 201), f"Create source failed: {new_source_res.text}"
        new_source = new_source_res.json()
        print(f"Created source: {new_source['code']}, production_suitable={new_source['is_production_suitable']}")

        # Verify the source
        ver_src_res = client.post(f"/api/v1/sources/{new_source['id']}/verify", headers=headers)
        assert ver_src_res.status_code == 200, f"Verify source failed: {ver_src_res.text}"
        print(f"Verified source {new_source['code']}: production_suitable={ver_src_res.json()['is_production_suitable']}")

        print("\n--- 5. Testing Ingestion Jobs ---")
        jobs_res = client.get("/api/v1/ingestion/jobs?page=1&page_size=20", headers=headers)
        assert jobs_res.status_code == 200, f"List ingestion jobs failed: {jobs_res.text}"
        jobs = jobs_res.json()["items"]
        print(f"Found {len(jobs)} ingestion jobs.")

        # Review an ingestion job
        unreviewed_job = next((j for j in jobs if j["review_status"] == "unreviewed" and j["status"] == "completed"), None)
        if unreviewed_job:
            rev_job_res = client.post(f"/api/v1/ingestion/jobs/{unreviewed_job['id']}/review", json={"review_status": "approved"}, headers=headers)
            assert rev_job_res.status_code == 200, f"Review job failed: {rev_job_res.text}"
            print(f"Reviewed job {unreviewed_job['id']}: review_status is now {rev_job_res.json()['review_status']}")
        else:
            print("No completed unreviewed jobs available to review.")

        print("\n--- 6. Testing Knowledge Entities, Provenance & Embedding Sync ---")
        for ent_type in ["disease", "symptom", "investigation", "medicine"]:
            ent_res = client.get(f"/api/v1/knowledge/{ent_type}/pending?page=1&page_size=20", headers=headers)
            assert ent_res.status_code == 200, f"List pending {ent_type} failed: {ent_res.text}"
            items = ent_res.json()["items"]
            print(f"Pending {ent_type}s: {len(items)}")

        # Inspect provenance of a disease
        disease_res = client.get("/api/v1/knowledge/disease/pending?page=1&page_size=10", headers=headers)
        diseases = disease_res.json()["items"]
        if diseases:
            d = diseases[0]
            prov_res = client.get(f"/api/v1/knowledge/disease/{d['id']}/provenance", headers=headers)
            assert prov_res.status_code == 200, f"Inspect provenance failed: {prov_res.text}"
            print(f"Provenance for disease '{d['name']}': {prov_res.json()}")

            # Sync embedding
            embed_res = client.post(f"/api/v1/knowledge/disease/{d['id']}/embeddings/sync", headers=headers)
            assert embed_res.status_code == 200, f"Sync embedding failed: {embed_res.text}"
            print(f"Generated embedding for '{d['name']}': {embed_res.json()}")

            # Review knowledge entity
            review_res = client.post(f"/api/v1/knowledge/disease/{d['id']}/review", json={"new_status": "APPROVED"}, headers=headers)
            assert review_res.status_code == 200, f"Review knowledge failed: {review_res.text}"
            print(f"Approved disease '{d['name']}': status={review_res.json()['status']}")

        print("\n--- 7. Testing Datasets Registry, Validation & Approval ---")
        ds_res = client.get("/api/v1/datasets", headers=headers)
        assert ds_res.status_code == 200, f"List datasets failed: {ds_res.text}"
        datasets = ds_res.json()
        print(f"Found {len(datasets)} datasets.")

        # Register a new dataset
        new_ds_res = client.post("/api/v1/datasets", json={
            "name": f"test-dataset-{first_doc['id'][:6]}",
            "source": "Clinical Unit Test",
            "license": "Internal Research",
            "version": "1.0.0",
            "hash": "sha256-pending",
            "schema_def": {"required": ["text", "label"]},
            "intended_use": "Automated pipeline testing",
            "limitations": "Test sample only",
            "storage_path": "data/raw/sample.jsonl"
        }, headers=headers)
        assert new_ds_res.status_code in (200, 201), f"Register dataset failed: {new_ds_res.text}"
        test_ds = new_ds_res.json()
        print(f"Registered dataset: {test_ds['name']}, status={test_ds['approval_status']}")

        # Validate the dataset
        val_res = client.post(f"/api/v1/datasets/{test_ds['id']}/validate", headers=headers)
        assert val_res.status_code == 200, f"Validate dataset failed: {val_res.text}"
        print("Validation Result:", val_res.json())

        # Approve the dataset
        app_res = client.post(f"/api/v1/datasets/{test_ds['id']}/approve", headers=headers)
        assert app_res.status_code == 200, f"Approve dataset failed: {app_res.text}"
        print(f"Approved dataset: {app_res.json()['name']}, status={app_res.json()['approval_status']}")

        print("\n--- 8. Testing Evaluation Harness ---")
        evals_res = client.get("/api/v1/evaluations", headers=headers)
        assert evals_res.status_code == 200, f"List evaluations failed: {evals_res.text}"
        evals = evals_res.json()
        print(f"Found {len(evals)} evaluation runs.")

        # Trigger an evaluation run
        trig_res = client.post("/api/v1/evaluations", json={
            "dataset_id": test_ds["id"],
            "model_version": "baseline-v1-local"
        }, headers=headers)
        assert trig_res.status_code in (200, 201), f"Trigger evaluation failed: {trig_res.text}"
        run_id = trig_res.json()["id"]
        print(f"Triggered evaluation run: {run_id}, status={trig_res.json()['status']}")

        # Execute evaluation pipeline
        exec_res = client.post(f"/api/v1/evaluations/{run_id}/execute", headers=headers)
        assert exec_res.status_code == 200, f"Execute evaluation failed: {exec_res.text}"
        print("Pipeline execution status:", exec_res.json())

        # Get details
        detail_res = client.get(f"/api/v1/evaluations/{run_id}", headers=headers)
        assert detail_res.status_code == 200, f"Get evaluation details failed: {detail_res.text}"
        detail = detail_res.json()
        print(f"Evaluation metrics: {detail['metrics']}, total record results: {len(detail['results'])}")

        print("\n--- 9. Testing ML Experiments Tracking ---")
        exp_res = client.get("/api/v1/experiments", headers=headers)
        assert exp_res.status_code == 200, f"List experiments failed: {exp_res.text}"
        experiments = exp_res.json()
        print(f"Found {len(experiments)} ML experiments.")

        # Register a new experiment
        new_exp_res = client.post("/api/v1/experiments", json={
            "name": f"exp-live-test-{first_doc['id'][:6]}",
            "code_commit": "c3d4e5f67890123456789abcdef0123456789a0b",
            "dataset_version": "1.0.0",
            "dataset_hash": "sha256-test",
            "model_name": "clinical-bert-base",
            "configuration": {"learning_rate": 2e-5, "batch_size": 16},
            "random_seed": 42.0,
            "hardware": {"gpu": "1x NVIDIA A100"}
        }, headers=headers)
        assert new_exp_res.status_code in (200, 201), f"Register experiment failed: {new_exp_res.text}"
        exp = new_exp_res.json()
        print(f"Registered experiment: {exp['name']}, status={exp['status']}")

        # Finish the experiment
        finish_res = client.patch(f"/api/v1/experiments/{exp['id']}", json={
            "status": "completed",
            "metrics": {"f1_score": 0.951, "eval_loss": 0.075},
            "execution_duration_sec": 1820.0,
            "artifact_location": "s3://docassistiq-models/test-run/model.bin"
        }, headers=headers)
        assert finish_res.status_code == 200, f"Finish experiment failed: {finish_res.text}"
        print(f"Finished experiment: status={finish_res.json()['status']}, metrics={finish_res.json()['metrics']}")

        print("\n=======================================================")
        print("ALL ADMIN MODULE ENDPOINTS TESTED AND VERIFIED 100% OK!")
        print("=======================================================")

if __name__ == "__main__":
    main()
