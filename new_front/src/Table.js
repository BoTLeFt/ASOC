import React, { useState, useEffect } from "react";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { Rating } from "primereact/rating";
import { MultiSelect } from "primereact/multiselect";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';

const Table = () => {
  const [selectedProduct, setSelectedProduct] = useState(null);
  const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjcmVlcEBjcmVlcC5jb20ifQ.SvlL1y-O0ZiJIXhLeumXOjsxSfzIrozGh57ln8ROgkw"
  const [data, setData] = useState(null);
  const defaultColumns = [
    { field: "ruleid", header: "ruleid" }
    // { field: "quantity", header: "Quantity" }
  ];

  const columns = [
    { field: "author", header: "author" },
    { field: "message", header: "message" },
    { field: "commit_hash", header: "commit_hash" },
    { field: "status", header: "status" },
    { field: "ruleid", header: "ruleid" }
  ];

  const [visibleColumns, setVisibleColumns] = useState(defaultColumns);

  useEffect(() => {
    fetch("http://host.docker.internal:8080/data", {
      method: "GET",
      headers: {
        'Authorization': 'Bearer ' + token,
      },
    })
      .then(response => response.json())
      .then((usefulData) => {
        console.log(usefulData);
        setData(usefulData);
      })
      .catch((e) => {
        console.error(`An error occurred: ${e}`)
      });
  }, []);

  const onColumnToggle = (event) => {
    let selectedColumns = event.value;
    let orderedSelectedColumns = columns.filter((col) =>
      selectedColumns.some((sCol) => sCol.field === col.field)
    );

    setVisibleColumns(orderedSelectedColumns);
  };

  const header = (
    <MultiSelect
      value={visibleColumns}
      options={columns}
      optionLabel="header"
      onChange={onColumnToggle}
      className="w-full sm:w-20rem"
      display="chip"
    />
  );
  const footer = <p>Total data = {data ? data.length : 0}</p>;

  const ratingBodyTemplate = (rowData) => {
    return <Rating value={rowData.rating} readOnly cancel={false} />;
  };

  // const codeBodyTemplate = (rowData) => {
  //   const rawHTML = `
  //   <div className="Code">
  //       <pre>
  //         <code className={\`language-csharp\`}>${rowData.code_line}</code>
  //       </pre>
  //   </div>
  //   `
  //   return (
  //   <div>
  //     <div dangerouslySetInnerHTML={{ __html: rawHTML }}></div>
  //   </div>);
  // };
  const codeBodyTemplate = (rowData) => {
    return(<SyntaxHighlighter language="csharp">
      {rowData.code_line}
    </SyntaxHighlighter>)
  };

  return (
    <div className="table-wrapper">
      <h2 className="table-name">PrimeReact data table</h2>
      <DataTable
        value={data}
        responsiveLayout="scroll"
        size="normal"
        showGridlines
        stripedRows
        header={header}
        footer={footer}
        removableSort
        paginator
        paginatorTemplate="CurrentPageReport FirstPageLink PrevPageLink PageLinks
      NextPageLink LastPageLink"
        rows={5}
        selection={selectedProduct}
        onSelectionChange={(e) => setSelectedProduct(e.value)}
        dataKey="id"
        >
        <Column
          selectionMode="multiple"
          field="Select"
          header="Select"
          sortable></Column>
        
        {visibleColumns.map((col) => (
          <Column
            key={col.field}
            field={col.field}
            header={col.header}
            filter
            sortable
          />
        ))}
        <Column
          field="code_line"
          header="code_line"
          body={codeBodyTemplate}
          sortable>
        </Column>
        <Column
          field="rating"
          header="Rating"
          body={ratingBodyTemplate}
          sortable>
        </Column>

      </DataTable>
    </div>
  );
};

export default Table;
