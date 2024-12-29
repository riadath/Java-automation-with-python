import os
import re
import shutil
import subprocess

# Color codes for terminal output
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No color

# Directory structure constants
SRC_MAIN = "src/main/java"
SRC_TEST = "src/test/java"
BUILD_GRADLE_FILE = "build.gradle"
MAIN_FILE_NAME = "Main.java"
TEST_FILE_NAME = "MainTest.java"

# Cleanup function
def cleanup():
    print(f"{Colors.BLUE}Cleaning up build and src directories...{Colors.NC}")
    for directory in ["build", "src", ".gradle", "gradle",".ropeproject"]:
        shutil.rmtree(directory, ignore_errors=True)
    for file in ["gradlew", "gradlew.bat", BUILD_GRADLE_FILE]:
        if os.path.exists(file):
            os.remove(file)

# Find all Java files excluding specified patterns
def find_java_files():
    java_files = []
    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith(".java") and file != TEST_FILE_NAME and "build" not in root and ".gradle" not in root:
                java_files.append(os.path.join(root, file))
    return java_files

# Rename the public class in a Java file to "Main" and update all references
def rename_class_to_main(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    # Match the public class name
    match = re.search(r'public class ([A-Za-z0-9_]+)', content)
    if not match:
        print(f"Could not find public class in {file_path}")
        return

    original_class_name = match.group(1)
    print(f"Renaming class {original_class_name} in {file_path}")

    # Replace all occurrences of the original class name with "Main"
    updated_content = re.sub(rf'\b{original_class_name}\b', "Main", content)

    # Overwrite the file with the modified content
    with open(file_path, 'w') as f:
        f.write(updated_content)
def create_build_gradle():
    gradle_content = """plugins {
    id 'java'
    id 'jacoco'
}

repositories {
    mavenCentral()
}

dependencies {
    testImplementation 'org.junit.jupiter:junit-jupiter-api:5.9.2'
    testRuntimeOnly 'org.junit.jupiter:junit-jupiter-engine:5.9.2'
}

test {
    useJUnitPlatform()
    finalizedBy jacocoTestReport

    testLogging {
        events 'passed', 'skipped', 'failed'
        showExceptions true
        showCauses true
        showStackTraces true
    }
}

jacocoTestReport {
    reports {
        csv.required = true
        html.required = false
    }
    doLast {
        def coverageFile = new File("${buildDir}/reports/jacoco/test/jacocoTestReport.csv")
        if (coverageFile.exists()) {
            println \"\\nCode Coverage Summary\"
            println \"===================\\n\"
            def lines = coverageFile.readLines()
            if (lines.size() > 1) {
                def data = lines[1].split(',')
                def instructionsCoverage = ((data[4].toInteger() - data[3].toInteger()) * 100.0 / data[4].toInteger())
                println \"Instructions covered: ${String.format('%.2f', instructionsCoverage)}%\"
            }
            println \"===================\"
        }
    }
}
"""
    with open(BUILD_GRADLE_FILE, "w") as f:
        f.write(gradle_content)

# Run the Gradle commands
def run_gradle():
    subprocess.run(["gradle", "wrapper"], check=True)
    subprocess.run(["./gradlew", "test", "jacocoTestReport"], check=True)

# Main testing function
def run_tests():
    os.makedirs(SRC_MAIN, exist_ok=True)
    os.makedirs(SRC_TEST, exist_ok=True)

    # Copy the test file
    shutil.copy(TEST_FILE_NAME, os.path.join(SRC_TEST, TEST_FILE_NAME))

    # Process each Java file
    for file in find_java_files():
        rename_class_to_main(file)

        print(f"{Colors.GREEN}Processing file: {file}{Colors.NC}")

        # Copy the renamed file to the target directory
        shutil.copy(file, os.path.join(SRC_MAIN, MAIN_FILE_NAME))

        # Create Gradle build script
        create_build_gradle()

        # Run Gradle commands
        try:
            run_gradle()
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}Error running tests for file: {file}{Colors.NC}")

        # Cleanup after each test
        cleanup()
        os.makedirs(SRC_MAIN, exist_ok=True)
        os.makedirs(SRC_TEST, exist_ok=True)
        shutil.copy(TEST_FILE_NAME, os.path.join(SRC_TEST, TEST_FILE_NAME))

# Entry point of the script
def main():
    print(f"{Colors.GREEN}Starting Java code testing...{Colors.NC}")

    # Find and rename Java classes to Main
    for file in find_java_files():
        rename_class_to_main(file)

    # Proceed with the renamed files
    run_tests()

    # Final cleanup
    print(f"{Colors.GREEN}All tests completed.{Colors.NC}")
    cleanup()

if __name__ == "__main__":
    main()
