#include "protobuf.h"

const char *describeFormat(Format format) {
    switch (format) {
        case Format::PROTOBUF_TEXTUAL: return "Protobuf Textual";
        case Format::PROTOBUF_BINARY: return "Protobuf Binary";
        case Format::JSON: return "JSON";
    }
}

void write(const kpex::tech::Technology &tech,
           const std::string &outputPath,
           Format format)
{
    std::cout << "Writing technology protobuf message to file '" << outputPath << "' "
              << "in " << describeFormat(format) << " format." << std::endl;
    
    switch (format) {
        case Format::PROTOBUF_TEXTUAL: {
            std::ofstream output(outputPath, std::ios::out | std::ios::binary);
            output << "# proto-file: tech.proto" << std::endl
                   << "# proto-message: kpex.tech.Technology" << std::endl << std::endl;
            google::protobuf::io::OstreamOutputStream zcos(&output);
            google::protobuf::TextFormat::Print(tech, &zcos);
            break;
        }

        case Format::PROTOBUF_BINARY: {
            std::ofstream output(outputPath, std::ios::out | std::ios::binary);
            tech.SerializeToOstream(&output);
            break;
        }
            
        case Format::JSON: {
            std::string jsonString;
            google::protobuf::util::JsonPrintOptions options;
            options.add_whitespace = true;
            options.preserve_proto_field_names = true;
            auto status =
                google::protobuf::util::MessageToJsonString(tech, &jsonString, options);
            std::ofstream output(outputPath, std::ios::out | std::ios::binary);
            output << jsonString;
            output.close();
            break;
        }
    }
}

void read(kpex::tech::Technology *tech,
          const std::string &inputPath,
          Format format)
{
    std::cout << "Reading technology protobuf message from file '" << inputPath << "' "
              << "in " << describeFormat(format) << " format." << std::endl;
    
    switch (format) {
        case Format::PROTOBUF_TEXTUAL: {
            std::fstream input(inputPath, std::ios::in);
            google::protobuf::io::IstreamInputStream fis(&input);
            google::protobuf::TextFormat::Parse(&fis, tech);
            break;
        }
            
        case Format::PROTOBUF_BINARY: {
            std::fstream input(inputPath, std::ios::in | std::ios::binary);
            tech->ParseFromIstream(&input);
            break;
        }
        
        case Format::JSON: {
            google::protobuf::util::JsonParseOptions options;

            std::fstream input(inputPath, std::ios::in);
            std::ostringstream buffer;
            buffer << input.rdbuf();
            auto status =
                google::protobuf::util::JsonStringToMessage(buffer.str(), tech, options);
            break;
        }
    }
}

void convert(const std::string &inputPath,
             Format inputFormat,
             const std::string &outputPath,
             Format outputFormat)
{
    std::cout << "Converting ..." << std::endl;
    
    kpex::tech::Technology tech;
    read(&tech, inputPath, inputFormat);
    write(tech, outputPath, outputFormat);
}

void addLayer(kpex::tech::Technology *tech,
              const std::string &name,
              uint32_t gds_layer,
              uint32_t gds_datatype,
              const std::string &description)
{
    kpex::tech::LayerInfo *layer = tech->add_layers();
    layer->set_name(name);
    layer->set_description(description);
    layer->set_gds_layer(gds_layer);
    layer->set_gds_datatype(gds_datatype);
}

void addComputedLayer(kpex::tech::Technology *tech,
                      kpex::tech::ComputedLayerInfo_Kind kind,
                      const std::string &name,
                      uint32_t gds_layer,
                      uint32_t gds_datatype,
                      const std::string &description)
{
    kpex::tech::ComputedLayerInfo *cl = tech->add_lvs_computed_layers();
    cl->set_kind(kind);
    kpex::tech::LayerInfo *layer = cl->mutable_layer_info();
    layer->set_name(name);
    layer->set_description(description);
    layer->set_gds_layer(gds_layer);
    layer->set_gds_datatype(gds_datatype);
}