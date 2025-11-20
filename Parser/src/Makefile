

CXX = g++
CXXFLAGS = -std=c++11 -O2
TARGET = HW1_n26142042
SRC = main.cpp parse_bench Writer.cpp
BENCH = benchmarks/adaptec1/adaptec1.aux

all: $(TARGET)

$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRC)

run: $(TARGET)
	@if [ ! -f $(BENCH) ]; then \
	    echo "Error: Benchmark file '$(BENCH)' not found!"; \
	    echo "Please put the .aux file in the correct folder."; \
	    exit 1; \
	fi
	@echo "Running $(TARGET) with $(BENCH) ..."
	./$(TARGET) $(BENCH)
	@echo "Generating layout PNG with gnuplot ..."
	@if [ -f _layout.plt ]; then gnuplot _layout.plt; else echo "Error: _layout.plt not found"; fi
	@echo "Done. Output files:"
	@ls -1 _chip.dat _pad.dat _pad_pin.dat _layout.plt _layout.png 2>/dev/null || true

clean:
	rm -f $(TARGET) _chip.dat _pad.dat _pad_pin.dat _layout.plt _layout.png


