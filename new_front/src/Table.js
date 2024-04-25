import React, { useState, useEffect } from "react";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { MultiSelect } from "primereact/multiselect";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { SelectButton } from 'primereact/selectbutton';

const Table = () => {
  const [selectedProduct, setSelectedProduct] = useState(null);
  const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjcmVlcEBjcmVlcC5jb20ifQ.SvlL1y-O0ZiJIXhLeumXOjsxSfzIrozGh57ln8ROgkw"
  const [data, setData] = useState(null);
  const defaultColumns = [
    { field: "ruleid", header: "ruleid" }
  ];

  const columns = [
    { field: "author", header: "author" },
    { field: "message", header: "message" },
    { field: "commit_hash", header: "commit_hash" },
    { field: "status", header: "status" },
    { field: "ruleid", header: "ruleid" }
  ];

  const [visibleColumns, setVisibleColumns] = useState(defaultColumns);

  const statusSelectItems = [
    {label: 'Created', value: 'created'},
    {label: 'False Positive', value: 'False Positive'},
    {label: 'True Positive', value: 'True Positive'},
    {label: 'Need review', value: 'Need review'},
    {label: 'Fixed', value: 'Fixed'}
  ];

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

  // const statusChangeBodyTemplate = (rowData) => {
  //   return <SelectButton value={rowData.status} options={statusSelectItems} onChange={(e) => e.value}></SelectButton>;
  // };
  const statusChangeBodyTemplate = (rowData) => {
    const handleChange = (e) => {
      const newStatus = e.value;
      const updatedData = [...data];
      const rowIndex = updatedData.findIndex(item => item.id === rowData.id);
      updatedData[rowIndex].status = newStatus;
      setData(updatedData);
  
      const requestOptions = {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify({ matchBasedId: updatedData[rowIndex].matchbasedid, status:  updatedData[rowIndex].status})
      };
      fetch('http://host.docker.internal:8080/change_status', requestOptions)
        .then(response => {
          console.log('Status updated successfully:', updatedData[rowIndex].status);
        })
        .catch(error => {
          console.error('Error updating status:', error);
        });
    };
  
    return (
      <SelectButton
        value={rowData.status}
        options={statusSelectItems}
        onChange={handleChange}
      />
    );
  };

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
          field="status"
          header="Change status"
          body={statusChangeBodyTemplate}
          sortable>
        </Column>

      </DataTable>
    </div>
  );
};

export default Table;
