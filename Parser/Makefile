# Makefile for HW1_n26142042

CXX = g++
CXXFLAGS = -std=c++11 -O2
TARGET = #Your output filename
SRC = main.cpp src/Writer.cpp
BENCH = benchmarks/bigblue4/bigblue4.aux

# 編譯程式
all: $(TARGET)

$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRC)

# 安全執行，檢查檔案並生成圖
run: $(TARGET)
	@chmod +x $(TARGET)
	@if [ ! -f $(BENCH) ]; then \
	    echo "Error: Benchmark file '$(BENCH)' not found!"; \
	    exit 1; \
	fi
	@echo "Running $(TARGET) with $(BENCH) ..."
	./$(TARGET) $(BENCH)
	@if [ -f _layout.plt ]; then \
	    echo "Generating _layout.png with gnuplot ..."; \
	    gnuplot _layout.plt; \
	fi
	@echo "Done."

# 清理生成檔案
clean:
	rm -f $(TARGET) _chip.dat _pad.dat _pad_pin.dat _layout.plt _layout.png

