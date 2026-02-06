#!/usr/bin/env python
"""Integration tests for the Legal Tabular Review API"""
import os
import sys
import json
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("=== TEST: Health Check ===")
    try:
        r = urllib.request.urlopen(f"{BASE_URL}/health")
        assert r.status == 200
        print("PASSED")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_list_templates():
    """Test templates listing"""
    print("\n=== TEST: List Templates ===")
    try:
        r = urllib.request.urlopen(f"{BASE_URL}/api/templates")
        data = json.loads(r.read().decode())
        print(f"  Templates: {len(data.get('templates', []))}")
        assert r.status == 200
        print("PASSED")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_list_documents():
    """Test documents listing"""
    print("\n=== TEST: List Documents ===")
    try:
        r = urllib.request.urlopen(f"{BASE_URL}/api/documents")
        data = json.loads(r.read().decode())
        print(f"  Documents: {len(data.get('documents', []))}")
        assert r.status == 200
        print("PASSED")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_list_projects():
    """Test projects listing"""
    print("\n=== TEST: List Projects ===")
    try:
        r = urllib.request.urlopen(f"{BASE_URL}/api/projects")
        data = json.loads(r.read().decode())
        print(f"  Projects: {len(data.get('projects', []))}")
        assert r.status == 200
        print("PASSED")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_search():
    """Test search endpoint"""
    print("\n=== TEST: Search Endpoint ===")
    try:
        r = urllib.request.urlopen(f"{BASE_URL}/api/search?q=test")
        data = json.loads(r.read().decode())
        print(f"  Results: {data.get('total', 0)}")
        assert r.status == 200
        print("PASSED")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_field_types():
    """Test field types endpoint"""
    print("\n=== TEST: Field Types ===")
    try:
        r = urllib.request.urlopen(f"{BASE_URL}/api/search/field-types")
        data = json.loads(r.read().decode())
        print(f"  Types: {data.get('field_types', [])}")
        assert r.status == 200
        print("PASSED")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_create_project():
    """Test project creation"""
    print("\n=== TEST: Create Project ===")
    try:
        data = json.dumps({
            "name": "Test Project",
            "description": "Integration test project",
            "template_id": 1
        }).encode()
        req = urllib.request.Request(
            f"{BASE_URL}/api/projects",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        r = urllib.request.urlopen(req)
        result = json.loads(r.read().decode())
        print(f"  Created project ID: {result.get('id')}")
        assert r.status == 200
        print("PASSED")
        return result.get('id')
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"FAILED: {e.code} - {body}")
        return None
    except Exception as e:
        print(f"FAILED: {e}")
        return None

def test_upload_documents():
    """Test document upload via API using multipart form"""
    print("\n=== TEST: Upload Documents ===")
    import mimetypes
    
    # First check if documents exist
    try:
        r = urllib.request.urlopen(f"{BASE_URL}/api/documents")
        data = json.loads(r.read().decode())
        existing = data.get('documents', [])
        if existing:
            print(f"  Documents already exist: {len(existing)}")
            for d in existing:
                print(f"    - ID {d['id']}: {d['original_filename']}")
            print("PASSED (using existing)")
            return [d['id'] for d in existing]
    except:
        pass
    
    # Upload sample files via API
    sample_files = [
        '/app/data/sample_nda.txt',
        '/app/data/sample_contract.txt',
        '/app/data/sample_lease.txt'
    ]
    
    doc_ids = []
    for filepath in sample_files:
        if os.path.exists(filepath):
            filename = os.path.basename(filepath)
            with open(filepath, 'rb') as f:
                content = f.read()
            
            # Create multipart form data
            boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
            body = (
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="files"; filename="{filename}"\r\n'
                f'Content-Type: text/plain\r\n\r\n'
            ).encode() + content + f'\r\n--{boundary}--\r\n'.encode()
            
            req = urllib.request.Request(
                f"{BASE_URL}/api/documents/upload",
                data=body,
                headers={
                    'Content-Type': f'multipart/form-data; boundary={boundary}'
                },
                method="POST"
            )
            
            try:
                r = urllib.request.urlopen(req)
                result = json.loads(r.read().decode())
                uploaded = result.get('uploaded', result.get('documents', []))
                if uploaded:
                    doc_id = uploaded[0].get('id') if isinstance(uploaded[0], dict) else uploaded[0]
                    doc_ids.append(doc_id)
                    print(f"  Uploaded: {filename} (ID: {doc_id})")
            except urllib.error.HTTPError as e:
                print(f"  Upload failed for {filename}: {e.code}")
    
    if doc_ids:
        print("PASSED")
    else:
        print("FAILED: No documents uploaded")
    return doc_ids

def test_add_documents_to_project(project_id, doc_ids):
    """Test adding documents to project"""
    print("\n=== TEST: Add Documents to Project ===")
    try:
        data = json.dumps({"document_ids": doc_ids}).encode()
        req = urllib.request.Request(
            f"{BASE_URL}/api/projects/{project_id}/documents",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        r = urllib.request.urlopen(req)
        result = json.loads(r.read().decode())
        print(f"  Added {len(doc_ids)} documents")
        assert r.status == 200
        print("PASSED")
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"FAILED: {e.code} - {body}")
        return False
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_run_extraction(project_id):
    """Test extraction"""
    print("\n=== TEST: Run Extraction ===")
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/api/projects/{project_id}/extract",
            data=b'',
            method="POST"
        )
        r = urllib.request.urlopen(req)
        result = json.loads(r.read().decode())
        print(f"  Extracted {result.get('count', 0)} values")
        assert r.status == 200
        print("PASSED")
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"FAILED: {e.code} - {body}")
        return False
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_get_values(project_id):
    """Test getting extracted values"""
    print("\n=== TEST: Get Extracted Values ===")
    try:
        r = urllib.request.urlopen(f"{BASE_URL}/api/projects/{project_id}/values")
        data = json.loads(r.read().decode())
        values = data.get('values', [])
        print(f"  Total values: {len(values)}")
        if values:
            print(f"  Sample value: {values[0].get('normalized_value', 'N/A')}")
        assert r.status == 200
        print("PASSED")
        return values
    except Exception as e:
        print(f"FAILED: {e}")
        return []

def test_approve_value(value_id):
    """Test approving a value"""
    print("\n=== TEST: Approve Value ===")
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/api/projects/values/{value_id}/approve",
            data=b'',
            method="POST"
        )
        r = urllib.request.urlopen(req)
        result = json.loads(r.read().decode())
        print(f"  Status: {result.get('status')}")
        assert result.get('status') == 'approved'
        print("PASSED")
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"FAILED: {e.code} - {body}")
        return False
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_reject_value(value_id):
    """Test rejecting a value"""
    print("\n=== TEST: Reject Value ===")
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/api/projects/values/{value_id}/reject",
            data=b'',
            method="POST"
        )
        r = urllib.request.urlopen(req)
        result = json.loads(r.read().decode())
        print(f"  Status: {result.get('status')}")
        assert result.get('status') == 'rejected'
        print("PASSED")
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"FAILED: {e.code} - {body}")
        return False
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_export_csv(project_id):
    """Test CSV export"""
    print("\n=== TEST: Export CSV ===")
    try:
        r = urllib.request.urlopen(f"{BASE_URL}/api/projects/{project_id}/export/csv")
        content = r.read().decode()
        print(f"  CSV size: {len(content)} bytes")
        print(f"  First line: {content.split(chr(10))[0][:80]}...")
        assert r.status == 200
        print("PASSED")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_export_excel(project_id):
    """Test Excel export"""
    print("\n=== TEST: Export Excel ===")
    try:
        r = urllib.request.urlopen(f"{BASE_URL}/api/projects/{project_id}/export/excel")
        content = r.read()
        print(f"  Excel size: {len(content)} bytes")
        assert r.status == 200
        assert len(content) > 0
        print("PASSED")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_validation(project_id):
    """Test validation endpoint"""
    print("\n=== TEST: Validation Summary ===")
    try:
        r = urllib.request.urlopen(f"{BASE_URL}/api/validation/projects/{project_id}/summary")
        data = json.loads(r.read().decode())
        print(f"  Summary: {data}")
        assert r.status == 200
        print("PASSED")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_audit_log(project_id):
    """Test audit log endpoint"""
    print("\n=== TEST: Audit Log ===")
    try:
        r = urllib.request.urlopen(f"{BASE_URL}/api/audit/projects/{project_id}")
        data = json.loads(r.read().decode())
        logs = data.get('logs', [])
        print(f"  Log entries: {len(logs)}")
        assert r.status == 200
        print("PASSED")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def main():
    print("=" * 60)
    print("LEGAL TABULAR REVIEW - INTEGRATION TESTS")
    print("=" * 60)
    
    results = {}
    
    # Basic API tests
    results['health'] = test_health()
    results['templates'] = test_list_templates()
    results['documents_list'] = test_list_documents()
    results['projects_list'] = test_list_projects()
    results['search'] = test_search()
    results['field_types'] = test_field_types()
    
    # Workflow tests
    doc_ids = test_upload_documents()
    results['upload'] = len(doc_ids) > 0
    
    project_id = test_create_project()
    results['create_project'] = project_id is not None
    
    if project_id and doc_ids:
        results['add_docs'] = test_add_documents_to_project(project_id, doc_ids)
        results['extraction'] = test_run_extraction(project_id)
        
        values = test_get_values(project_id)
        results['get_values'] = len(values) > 0
        
        if values:
            results['approve'] = test_approve_value(values[0]['id'])
            if len(values) > 1:
                results['reject'] = test_reject_value(values[1]['id'])
            else:
                results['reject'] = True
        
        results['export_csv'] = test_export_csv(project_id)
        results['export_excel'] = test_export_excel(project_id)
        results['validation'] = test_validation(project_id)
        results['audit_log'] = test_audit_log(project_id)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {test}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())

