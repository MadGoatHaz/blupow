#!/usr/bin/env python3
"""
AiCockpit Comprehensive Diagnostics System
==========================================

Advanced diagnostic and testing system for AiCockpit based on proven 
methodologies from the BluPow project, adapted for AI agent orchestration
and backend/frontend integration.

This tool provides comprehensive testing of:
- Backend API endpoints and services
- Frontend-backend integration
- AI model loading and inference
- Agent execution and orchestration
- Development environment health
- Database and session management

Usage:
    python3 scripts/acp_diagnostics.py [--test TEST] [--json] [--quiet]
    python3 scripts/acp_diagnostics.py --interactive
    
Tests: backend, frontend, models, agents, integration, all

Author: AiCockpit Development Team  
License: GPL-3.0
"""

import os
import sys
import json
import argparse
import asyncio
import aiohttp
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import time

@dataclass
class DiagnosticResult:
    """Structured result object for diagnostic operations."""
    test_name: str
    status: str  # PASS, FAIL, SKIP, WARNING
    duration_ms: int
    message: str
    details: Dict[str, Any]
    timestamp: str
    recommendations: List[str]

class AiCockpitDiagnostics:
    """Comprehensive diagnostics for AiCockpit project."""
    
    def __init__(self, project_root: Path, backend_url: str = "http://localhost:8000"):
        self.project_root = project_root
        self.backend_url = backend_url
        self.backend_root = project_root / "acp_backend"
        self.frontend_root = project_root / "acp_frontend"
        
    async def test_backend_health(self) -> DiagnosticResult:
        """Test backend API health and basic endpoints."""
        start_time = time.time()
        details = {}
        recommendations = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test health endpoint
                try:
                    async with session.get(f"{self.backend_url}/health", timeout=5) as response:
                        if response.status == 200:
                            health_data = await response.json()
                            details["health_endpoint"] = health_data
                            details["backend_responsive"] = True
                        else:
                            details["health_endpoint_status"] = response.status
                            details["backend_responsive"] = False
                            recommendations.append("Check backend server status and configuration")
                except asyncio.TimeoutError:
                    details["backend_responsive"] = False
                    recommendations.append("Backend server appears to be down or unresponsive")
                
                # Test API documentation
                try:
                    async with session.get(f"{self.backend_url}/docs", timeout=5) as response:
                        details["docs_available"] = response.status == 200
                except:
                    details["docs_available"] = False
                    recommendations.append("API documentation endpoint not accessible")
                
                # Test LLM endpoints
                try:
                    async with session.get(f"{self.backend_url}/llm/models", timeout=10) as response:
                        if response.status == 200:
                            models_data = await response.json()
                            details["available_models"] = len(models_data.get("models", []))
                            details["llm_service_active"] = True
                        else:
                            details["llm_service_active"] = False
                            recommendations.append("LLM service may not be properly configured")
                except Exception as e:
                    details["llm_service_error"] = str(e)
                    details["llm_service_active"] = False
                
                # Test session management
                try:
                    async with session.get(f"{self.backend_url}/sessions", timeout=5) as response:
                        if response.status == 200:
                            sessions_data = await response.json()
                            details["session_service_active"] = True
                            details["active_sessions"] = len(sessions_data.get("sessions", []))
                        else:
                            details["session_service_active"] = False
                except Exception as e:
                    details["session_service_error"] = str(e)
                    details["session_service_active"] = False
        
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            return DiagnosticResult(
                test_name="backend_health",
                status="FAIL",
                duration_ms=duration,
                message=f"Backend health check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                recommendations=["Ensure backend server is running", "Check backend configuration"]
            )
        
        duration = int((time.time() - start_time) * 1000)
        
        # Determine overall status
        backend_up = details.get("backend_responsive", False)
        critical_services = details.get("llm_service_active", False) and details.get("session_service_active", False)
        
        if backend_up and critical_services:
            status = "PASS"
            message = "Backend services are healthy and responsive"
        elif backend_up:
            status = "WARNING"
            message = "Backend is responsive but some services may have issues"
        else:
            status = "FAIL"
            message = "Backend is not responsive or has critical issues"
            recommendations.append("Start the backend server: pdm run dev")
        
        return DiagnosticResult(
            test_name="backend_health",
            status=status,
            duration_ms=duration,
            message=message,
            details=details,
            timestamp=datetime.now().isoformat(),
            recommendations=recommendations
        )
    
    async def test_frontend_health(self) -> DiagnosticResult:
        """Test frontend development server and build health."""
        start_time = time.time()
        details = {}
        recommendations = []
        
        try:
            # Check if frontend directory exists
            if not self.frontend_root.exists():
                duration = int((time.time() - start_time) * 1000)
                return DiagnosticResult(
                    test_name="frontend_health",
                    status="FAIL",
                    duration_ms=duration,
                    message="Frontend directory not found",
                    details={"frontend_path": str(self.frontend_root)},
                    timestamp=datetime.now().isoformat(),
                    recommendations=["Ensure frontend directory exists and is properly set up"]
                )
            
            # Check package.json
            package_json = self.frontend_root / "package.json"
            if package_json.exists():
                try:
                    with open(package_json, 'r') as f:
                        package_data = json.load(f)
                        details["package_json_valid"] = True
                        details["project_name"] = package_data.get("name", "unknown")
                        details["dependencies_count"] = len(package_data.get("dependencies", {}))
                        details["dev_dependencies_count"] = len(package_data.get("devDependencies", {}))
                except Exception as e:
                    details["package_json_error"] = str(e)
                    recommendations.append("Fix package.json syntax errors")
            else:
                details["package_json_exists"] = False
                recommendations.append("Create package.json for frontend project")
            
            # Check node_modules
            node_modules = self.frontend_root / "node_modules"
            details["node_modules_installed"] = node_modules.exists()
            if not node_modules.exists():
                recommendations.append("Run 'npm install' in frontend directory")
            
            # Check Next.js configuration
            next_config = self.frontend_root / "next.config.js"
            details["next_config_exists"] = next_config.exists()
            
            # Check TypeScript configuration
            tsconfig = self.frontend_root / "tsconfig.json"
            details["typescript_config_exists"] = tsconfig.exists()
            
            # Try to connect to frontend dev server
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://localhost:3000", timeout=3) as response:
                        details["dev_server_responsive"] = response.status == 200
                        details["dev_server_status"] = response.status
            except:
                details["dev_server_responsive"] = False
                recommendations.append("Start frontend dev server: npm run dev")
            
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            return DiagnosticResult(
                test_name="frontend_health",
                status="FAIL",
                duration_ms=duration,
                message=f"Frontend health check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                recommendations=["Check frontend setup and configuration"]
            )
        
        duration = int((time.time() - start_time) * 1000)
        
        # Determine status
        has_config = details.get("package_json_valid", False) and details.get("next_config_exists", False)
        has_deps = details.get("node_modules_installed", False)
        server_up = details.get("dev_server_responsive", False)
        
        if has_config and has_deps and server_up:
            status = "PASS"
            message = "Frontend is healthy and development server is running"
        elif has_config and has_deps:
            status = "WARNING"
            message = "Frontend is configured but development server is not running"
        else:
            status = "FAIL"
            message = "Frontend has configuration or dependency issues"
        
        return DiagnosticResult(
            test_name="frontend_health",
            status=status,
            duration_ms=duration,
            message=message,
            details=details,
            timestamp=datetime.now().isoformat(),
            recommendations=recommendations
        )
    
    async def test_model_loading(self) -> DiagnosticResult:
        """Test AI model loading and inference capabilities."""
        start_time = time.time()
        details = {}
        recommendations = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get available models
                try:
                    async with session.get(f"{self.backend_url}/llm/models", timeout=10) as response:
                        if response.status == 200:
                            models_data = await response.json()
                            available_models = models_data.get("models", [])
                            details["available_models"] = len(available_models)
                            details["model_list"] = [m.get("id", "unknown") for m in available_models[:5]]
                            
                            if not available_models:
                                recommendations.append("Add GGUF models to the models directory")
                                recommendations.append("Check MODELS_DIR configuration in .env")
                        else:
                            details["models_endpoint_error"] = response.status
                            recommendations.append("Check LLM service configuration")
                except Exception as e:
                    details["models_fetch_error"] = str(e)
                    recommendations.append("Ensure backend LLM service is running")
                
                # Test model loading (if models available)
                if details.get("available_models", 0) > 0:
                    try:
                        # Try to get current loaded model
                        async with session.get(f"{self.backend_url}/llm/current-model", timeout=5) as response:
                            if response.status == 200:
                                current_model = await response.json()
                                details["current_model_loaded"] = current_model.get("model_id") is not None
                                details["current_model_id"] = current_model.get("model_id", "none")
                            else:
                                details["current_model_loaded"] = False
                    except Exception as e:
                        details["current_model_error"] = str(e)
                
                # Test simple inference (if model is loaded)
                if details.get("current_model_loaded", False):
                    try:
                        test_payload = {
                            "messages": [{"role": "user", "content": "Hello, this is a test."}],
                            "max_tokens": 10,
                            "temperature": 0.1
                        }
                        async with session.post(
                            f"{self.backend_url}/llm/chat/completions",
                            json=test_payload,
                            timeout=30
                        ) as response:
                            if response.status == 200:
                                details["inference_test_passed"] = True
                                # For streaming response, just check if we get data
                                async for line in response.content:
                                    if line.strip():
                                        details["inference_response_received"] = True
                                        break
                            else:
                                details["inference_test_passed"] = False
                                details["inference_error_status"] = response.status
                    except Exception as e:
                        details["inference_test_error"] = str(e)
                        recommendations.append("Check model inference configuration")
        
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            return DiagnosticResult(
                test_name="model_loading",
                status="FAIL",
                duration_ms=duration,
                message=f"Model loading test failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                recommendations=["Ensure backend is running and LLM service is configured"]
            )
        
        duration = int((time.time() - start_time) * 1000)
        
        # Determine status
        has_models = details.get("available_models", 0) > 0
        model_loaded = details.get("current_model_loaded", False)
        inference_works = details.get("inference_test_passed", False)
        
        if has_models and model_loaded and inference_works:
            status = "PASS"
            message = f"Model system healthy - {details.get('available_models', 0)} models available, inference working"
        elif has_models and model_loaded:
            status = "WARNING"
            message = "Models available and loaded but inference test had issues"
        elif has_models:
            status = "WARNING"
            message = "Models available but none currently loaded"
            recommendations.append("Load a model for testing: check /llm/load endpoint")
        else:
            status = "FAIL"
            message = "No models available for loading"
        
        return DiagnosticResult(
            test_name="model_loading",
            status=status,
            duration_ms=duration,
            message=message,
            details=details,
            timestamp=datetime.now().isoformat(),
            recommendations=recommendations
        )
    
    async def test_agent_system(self) -> DiagnosticResult:
        """Test AI agent execution and orchestration."""
        start_time = time.time()
        details = {}
        recommendations = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test agent configurations endpoint
                try:
                    async with session.get(f"{self.backend_url}/agents/configs", timeout=5) as response:
                        if response.status == 200:
                            configs_data = await response.json()
                            details["agent_configs_available"] = len(configs_data.get("configs", []))
                            details["agent_service_responsive"] = True
                        else:
                            details["agent_service_responsive"] = False
                            details["agent_configs_error"] = response.status
                            recommendations.append("Check agent service configuration")
                except Exception as e:
                    details["agent_service_error"] = str(e)
                    details["agent_service_responsive"] = False
                    recommendations.append("Ensure agent service is properly initialized")
                
                # Test agent execution (if configs available)
                if details.get("agent_configs_available", 0) > 0:
                    try:
                        # Try a simple agent execution test
                        test_payload = {
                            "agent_id": "test-agent",
                            "goal": "Say hello and confirm you are working",
                            "max_iterations": 1
                        }
                        async with session.post(
                            f"{self.backend_url}/agents/run/stream",
                            json=test_payload,
                            timeout=15
                        ) as response:
                            if response.status == 200:
                                details["agent_execution_test"] = "PASS"
                                # Check if we get streaming response
                                first_chunk = await response.content.read(100)
                                details["agent_streaming_works"] = len(first_chunk) > 0
                            else:
                                details["agent_execution_test"] = "FAIL"
                                details["agent_execution_error"] = response.status
                                recommendations.append("Check agent execution configuration")
                    except Exception as e:
                        details["agent_execution_error"] = str(e)
                        recommendations.append("Verify agent dependencies (smol_dev, etc.)")
        
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            return DiagnosticResult(
                test_name="agent_system",
                status="FAIL",
                duration_ms=duration,
                message=f"Agent system test failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                recommendations=["Ensure backend agent service is running"]
            )
        
        duration = int((time.time() - start_time) * 1000)
        
        # Determine status
        service_up = details.get("agent_service_responsive", False)
        has_configs = details.get("agent_configs_available", 0) > 0
        execution_works = details.get("agent_execution_test") == "PASS"
        
        if service_up and has_configs and execution_works:
            status = "PASS"
            message = f"Agent system healthy - {details.get('agent_configs_available', 0)} configs available, execution working"
        elif service_up and has_configs:
            status = "WARNING"
            message = "Agent service responsive but execution may have issues"
        elif service_up:
            status = "WARNING"
            message = "Agent service responsive but no configurations found"
            recommendations.append("Create agent configurations in default_session_agents.json")
        else:
            status = "FAIL"
            message = "Agent service is not responsive"
        
        return DiagnosticResult(
            test_name="agent_system",
            status=status,
            duration_ms=duration,
            message=message,
            details=details,
            timestamp=datetime.now().isoformat(),
            recommendations=recommendations
        )
    
    async def test_integration_flow(self) -> DiagnosticResult:
        """Test end-to-end integration between frontend and backend."""
        start_time = time.time()
        details = {}
        recommendations = []
        
        try:
            # Test key integration points
            integration_tests = []
            
            async with aiohttp.ClientSession() as session:
                # Test CORS configuration
                try:
                    async with session.options(f"{self.backend_url}/health") as response:
                        details["cors_configured"] = "Access-Control-Allow-Origin" in response.headers
                except Exception as e:
                    details["cors_test_error"] = str(e)
                    recommendations.append("Configure CORS for frontend-backend communication")
                
                # Test WebSocket endpoint (terminal service)
                try:
                    import websockets
                    ws_url = self.backend_url.replace("http://", "ws://") + "/terminals/new"
                    async with websockets.connect(ws_url, timeout=3) as websocket:
                        details["websocket_connection"] = True
                        await websocket.close()
                except Exception as e:
                    details["websocket_connection"] = False
                    details["websocket_error"] = str(e)
                    recommendations.append("Check WebSocket terminal service configuration")
                
                # Test file upload capability
                try:
                    # Create a test session first
                    session_payload = {
                        "name": "diagnostic-test-session",
                        "description": "Temporary session for diagnostics"
                    }
                    async with session.post(f"{self.backend_url}/sessions", json=session_payload) as response:
                        if response.status == 201:
                            session_data = await response.json()
                            test_session_id = session_data.get("session_id")
                            details["test_session_created"] = True
                            
                            # Test file operations
                            files_url = f"{self.backend_url}/workspaces/sessions/{test_session_id}/files"
                            async with session.get(files_url) as response:
                                if response.status == 200:
                                    details["file_operations_available"] = True
                                else:
                                    details["file_operations_available"] = False
                                    recommendations.append("Check workspace file service configuration")
                            
                            # Clean up test session
                            await session.delete(f"{self.backend_url}/sessions/{test_session_id}")
                        else:
                            details["test_session_created"] = False
                            recommendations.append("Session creation failed - check session service")
                except Exception as e:
                    details["integration_test_error"] = str(e)
                    recommendations.append("Check session and file management services")
        
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            return DiagnosticResult(
                test_name="integration_flow",
                status="FAIL",
                duration_ms=duration,
                message=f"Integration test failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                recommendations=["Ensure all backend services are running"]
            )
        
        duration = int((time.time() - start_time) * 1000)
        
        # Determine status
        cors_ok = details.get("cors_configured", False)
        websocket_ok = details.get("websocket_connection", False)
        files_ok = details.get("file_operations_available", False)
        session_ok = details.get("test_session_created", False)
        
        passed_tests = sum([cors_ok, websocket_ok, files_ok, session_ok])
        
        if passed_tests >= 3:
            status = "PASS"
            message = f"Integration flow healthy - {passed_tests}/4 tests passed"
        elif passed_tests >= 2:
            status = "WARNING"
            message = f"Integration partially working - {passed_tests}/4 tests passed"
        else:
            status = "FAIL"
            message = f"Integration has significant issues - only {passed_tests}/4 tests passed"
        
        return DiagnosticResult(
            test_name="integration_flow",
            status=status,
            duration_ms=duration,
            message=message,
            details=details,
            timestamp=datetime.now().isoformat(),
            recommendations=recommendations
        )
    
    async def run_comprehensive_diagnostics(self, tests: Optional[List[str]] = None) -> Dict[str, DiagnosticResult]:
        """Run comprehensive diagnostics across all systems."""
        all_tests = {
            "backend": self.test_backend_health,
            "frontend": self.test_frontend_health,
            "models": self.test_model_loading,
            "agents": self.test_agent_system,
            "integration": self.test_integration_flow
        }
        
        if tests:
            tests_to_run = {k: v for k, v in all_tests.items() if k in tests}
        else:
            tests_to_run = all_tests
        
        results = {}
        for test_name, test_func in tests_to_run.items():
            try:
                results[test_name] = await test_func()
            except Exception as e:
                results[test_name] = DiagnosticResult(
                    test_name=test_name,
                    status="FAIL",
                    duration_ms=0,
                    message=f"Test execution failed: {str(e)}",
                    details={"error": str(e)},
                    timestamp=datetime.now().isoformat(),
                    recommendations=["Check test configuration and try again"]
                )
        
        return results

def format_results_human(results: Dict[str, DiagnosticResult]) -> str:
    """Format diagnostic results for human-readable output."""
    output = []
    output.append("🔧 AiCockpit Comprehensive Diagnostics")
    output.append("=" * 50)
    output.append("")
    
    # Count status types
    passed = sum(1 for r in results.values() if r.status == "PASS")
    warnings = sum(1 for r in results.values() if r.status == "WARNING")
    failed = sum(1 for r in results.values() if r.status == "FAIL")
    
    status_emoji = {"PASS": "✅", "WARNING": "⚠️", "FAIL": "❌", "SKIP": "⏭️"}
    
    output.append(f"📊 Test Summary: {passed} passed, {warnings} warnings, {failed} failed")
    output.append("")
    
    for test_name, result in results.items():
        emoji = status_emoji.get(result.status, '❓')
        output.append(f"{emoji} {test_name.upper()}: {result.status} ({result.duration_ms}ms)")
        output.append(f"   {result.message}")
        
        if result.recommendations:
            output.append("   Recommendations:")
            for rec in result.recommendations:
                output.append(f"   → {rec}")
        
        output.append("")
    
    return "\n".join(output)

def format_results_brief(results: Dict[str, DiagnosticResult]) -> str:
    """Format diagnostic results for brief output."""
    passed = sum(1 for r in results.values() if r.status == "PASS")
    warnings = sum(1 for r in results.values() if r.status == "WARNING")
    failed = sum(1 for r in results.values() if r.status == "FAIL")
    
    status_emoji = {"PASS": "✅", "WARNING": "⚠️", "FAIL": "❌"}
    lines = [f"AiCockpit Diagnostics: {passed}✅ {warnings}⚠️ {failed}❌"]
    
    for test_name, result in results.items():
        emoji = status_emoji.get(result.status, '❓')
        lines.append(f"{test_name}: {emoji}")
    
    return " | ".join(lines)

def interactive_menu():
    """Interactive menu for diagnostics."""
    print("🔧 AiCockpit Interactive Diagnostics")
    print("=" * 40)
    print("1. Full System Diagnostics")
    print("2. Backend Health Check")
    print("3. Frontend Health Check") 
    print("4. Model Loading Test")
    print("5. Agent System Test")
    print("6. Integration Flow Test")
    print("7. Quick Health Summary")
    print("0. Exit")
    print()
    
    choice = input("Select option (0-7): ").strip()
    
    test_map = {
        "1": None,  # All tests
        "2": ["backend"],
        "3": ["frontend"],
        "4": ["models"],
        "5": ["agents"],
        "6": ["integration"],
        "7": "brief"
    }
    
    if choice == "0":
        return None
    elif choice in test_map:
        return test_map[choice]
    else:
        print("Invalid choice. Please try again.")
        return interactive_menu()

async def main():
    """Main entry point for the diagnostics system."""
    parser = argparse.ArgumentParser(
        description="AiCockpit Comprehensive Diagnostics System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/acp_diagnostics.py
  python3 scripts/acp_diagnostics.py --test backend models
  python3 scripts/acp_diagnostics.py --json --quiet
  python3 scripts/acp_diagnostics.py --interactive
        """
    )
    
    parser.add_argument(
        "--test", 
        nargs="+", 
        choices=["backend", "frontend", "models", "agents", "integration", "all"],
        help="Specific tests to run (default: all)"
    )
    parser.add_argument(
        "--json", 
        action="store_true", 
        help="Output results in JSON format (AI-friendly)"
    )
    parser.add_argument(
        "--quiet", 
        action="store_true", 
        help="Minimal output mode"
    )
    parser.add_argument(
        "--interactive", 
        action="store_true", 
        help="Interactive menu mode"
    )
    parser.add_argument(
        "--backend-url",
        default="http://localhost:8000",
        help="Backend URL for testing (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    # Determine project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    # Initialize diagnostics
    diagnostics = AiCockpitDiagnostics(project_root, args.backend_url)
    
    try:
        # Handle interactive mode
        if args.interactive:
            tests = interactive_menu()
            if tests is None:
                return
            elif tests == "brief":
                results = await diagnostics.run_comprehensive_diagnostics()
                print(format_results_brief(results))
                return
        else:
            tests = args.test
        
        # Determine tests to run
        if tests and "all" not in tests:
            test_list = tests
        else:
            test_list = None
        
        # Run diagnostics
        results = await diagnostics.run_comprehensive_diagnostics(test_list)
        
        # Output results
        if args.json:
            json_results = {k: asdict(v) for k, v in results.items()}
            print(json.dumps(json_results, indent=2))
        elif args.quiet:
            print(format_results_brief(results))
        else:
            print(format_results_human(results))
        
        # Set exit code based on results
        failed_tests = sum(1 for r in results.values() if r.status == "FAIL")
        warning_tests = sum(1 for r in results.values() if r.status == "WARNING")
        
        if failed_tests > 0:
            sys.exit(1)  # Error exit code
        elif warning_tests > 0:
            sys.exit(2)  # Warning exit code
        else:
            sys.exit(0)  # Success
            
    except Exception as e:
        if args.json:
            error_result = {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            print(json.dumps(error_result, indent=2))
        else:
            print(f"❌ Diagnostics failed: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 